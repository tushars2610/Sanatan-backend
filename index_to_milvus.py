import os
import sys
import uuid
import psycopg2
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from sentence_transformers import SentenceTransformer

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "spiritualsakha"),
    "user": os.environ.get("DB_USER", "sakha"),
    "password": os.environ.get("DB_PASSWORD", "sakha_dev_password"),
}

MILVUS_HOST = os.environ.get("MILVUS_HOST", "127.0.0.1")
MILVUS_PORT = os.environ.get("MILVUS_PORT", "19530")
COLLECTION_NAME = "ScripturePassages"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
DIMENSION = 384

def get_passages_from_postgres():
    conn = psycopg2.connect(**DB_CONFIG)
    passages = []
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id, 
                    p.chapter, 
                    p.verse_number, 
                    p.translation, 
                    p.summary, 
                    s.name as source_name,
                    array_remove(array_agg(t.id::text), NULL) as tag_ids
                FROM passages p
                JOIN sources s ON p.source_id = s.id
                LEFT JOIN passage_tags pt ON p.id = pt.passage_id
                LEFT JOIN tags t ON pt.tag_id = t.id
                GROUP BY p.id, p.chapter, p.verse_number, p.translation, p.summary, s.name;
            """)
            for row in cur.fetchall():
                passages.append({
                    "id": str(row[0]),
                    "chapter": row[1],
                    "verse_number": row[2],
                    "translation": row[3],
                    "summary": row[4],
                    "source_name": row[5],
                    "tag_ids": row[6] if row[6] else []
                })
    finally:
        conn.close()
    return passages

def setup_milvus_collection():
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    
    if utility.has_collection(COLLECTION_NAME):
        print(f"Dropping existing collection {COLLECTION_NAME}...")
        utility.drop_collection(COLLECTION_NAME)

    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
        FieldSchema(name="passage_id", dtype=DataType.VARCHAR, max_length=36),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIMENSION),
        FieldSchema(name="source_name", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="tag_ids", dtype=DataType.ARRAY, element_type=DataType.VARCHAR, max_length=36, max_capacity=20),
    ]

    schema = CollectionSchema(fields, description="Scripture passage embeddings")
    collection = Collection(name=COLLECTION_NAME, schema=schema)

    index_params = {
        "metric_type": "COSINE",
        "index_type": "HNSW",
        "params": {"M": 16, "efConstruction": 200}
    }
    
    print("Building index on Milvus collection...")
    collection.create_index(field_name="embedding", index_params=index_params)
    collection.load()
    return collection

def update_postgres_embeddings_record(passage_ids):
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            for pid in passage_ids:
                cur.execute("""
                    INSERT INTO passage_embeddings (passage_id, milvus_collection, embedding_model_version)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (passage_id) DO UPDATE SET
                        milvus_collection = EXCLUDED.milvus_collection,
                        embedding_model_version = EXCLUDED.embedding_model_version,
                        indexed_at = now()
                """, (pid, COLLECTION_NAME, EMBEDDING_MODEL_NAME))
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def main():
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    
    print("Fetching passages from Postgres...")
    passages = get_passages_from_postgres()
    if not passages:
        print("No passages found in Postgres. Did you run load_to_postgres.py?")
        sys.exit(1)
        
    print(f"Found {len(passages)} passages.")
    
    print("Setting up Milvus collection...")
    collection = setup_milvus_collection()
    
    print("Generating embeddings and inserting into Milvus...")
    
    data_to_insert = [
        [], # id
        [], # passage_id
        [], # embedding
        [], # source_name
        []  # tag_ids
    ]
    
    passage_ids = []
    
    for p in passages:
        # Combine translation and summary for richer embedding
        text_to_embed = f"{p['translation']} {p['summary']}"
        embedding = model.encode(text_to_embed).tolist()
        
        milvus_id = str(uuid.uuid4())
        data_to_insert[0].append(milvus_id)
        data_to_insert[1].append(p["id"])
        data_to_insert[2].append(embedding)
        data_to_insert[3].append(p["source_name"])
        data_to_insert[4].append(p["tag_ids"])
        
        passage_ids.append(p["id"])
        
    # Batch insert
    insert_result = collection.insert(data_to_insert)
    print(f"Inserted {insert_result.insert_count} entities into Milvus.")
    
    collection.flush()
    print(f"Collection {COLLECTION_NAME} now has {collection.num_entities} entities.")
    
    print("Updating Postgres tracking table...")
    update_postgres_embeddings_record(passage_ids)
    
    print("Done!")

if __name__ == "__main__":
    main()
