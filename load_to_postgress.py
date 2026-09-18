"""
load_to_postgres.py

Joins:
  - data/raw/all_verses.json           (has chapter, verse, slok/transliteration
                                         -- produced by fetch_gita_data.py)
  - data/categorized/all_tagged_verses.json  (has chapter, verse, siva_et,
                                         categories, summary, reviewed
                                         -- produced by categorize_gita_data.py)

...on (chapter, verse), then inserts one row per verse into `passages`
(translation = siva_et, sanskrit_text/transliteration from raw data),
and one row per (verse, category) into `passage_tags`.

Run this AFTER:
  1. docker compose up -d          (starts Postgres, applies init.sql on first run)
  2. fetch_gita_data.py            (produces data/raw/all_verses.json)
  3. categorize_gita_data.py       (produces data/categorized/all_tagged_verses.json)

Usage:
    pip install psycopg2-binary
    python load_to_postgres.py

Connection settings default to match docker-compose.yml; override via env
vars if you changed them there (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD).

IMPORTANT: This script only loads passages where "reviewed": true in
all_tagged_verses.json, UNLESS you pass --include-unreviewed. Per the PRD,
nothing should be treated as "live" scripture data without human review of
the tags and summary first. Loading unreviewed data is meant for local
testing only -- don't point a real chatbot at unreviewed rows.
"""

import argparse
import json
import os
import sys

import psycopg2
from psycopg2.extras import execute_values

RAW_PATH = "data/raw/all_verses.json"
TAGGED_PATH = "data/categorized/all_tagged_verses.json"

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
    "dbname": os.environ.get("DB_NAME", "spiritualsakha"),
    "user": os.environ.get("DB_USER", "sakha"),
    "password": os.environ.get("DB_PASSWORD", "sakha_dev_password"),
}

SOURCE_NAME = "Bhagavad Gita"
TRANSLATOR_NAME = "Swami Sivananda"


def load_json(path: str):
    if not os.path.exists(path):
        print(f"[error] Required file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_verse_map(raw_verses: list[dict]) -> dict[tuple[int, int], dict]:
    """Maps (chapter, verse) -> raw fields we need (sanskrit + transliteration)."""
    verse_map = {}
    for entry in raw_verses:
        chapter = entry.get("chapter")
        verse = entry.get("verse")
        if chapter is None or verse is None:
            continue
        verse_map[(chapter, verse)] = {
            "sanskrit_text": entry.get("slok"),
            "transliteration": entry.get("transliteration"),
        }
    return verse_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--include-unreviewed",
        action="store_true",
        help="Load rows even where reviewed=false (local testing only, not for production data).",
    )
    args = parser.parse_args()

    raw_verses = load_json(RAW_PATH)
    tagged_verses = load_json(TAGGED_PATH)

    verse_map = build_verse_map(raw_verses)
    print(f"Loaded {len(verse_map)} raw verses (Sanskrit + transliteration).")
    print(f"Loaded {len(tagged_verses)} categorized verses.")

    skipped_unreviewed = 0
    skipped_no_match = 0
    to_load = []

    for tv in tagged_verses:
        if not tv.get("reviewed", False) and not args.include_unreviewed:
            skipped_unreviewed += 1
            continue

        key = (tv["chapter"], tv["verse"])
        raw = verse_map.get(key)
        if raw is None:
            skipped_no_match += 1
            print(f"  [warn] no raw match for chapter {tv['chapter']}, "
                  f"verse {tv['verse']} -- skipping")
            continue

        to_load.append({
            "chapter": str(tv["chapter"]),
            "verse_number": f"{tv['chapter']}.{tv['verse']}",
            "sanskrit_text": raw["sanskrit_text"],
            "transliteration": raw["transliteration"],
            "translation": tv["siva_et"],
            "summary": tv.get("summary", ""),
            "reviewed": tv.get("reviewed", False),
            "categories": tv.get("categories", []),
        })

    if skipped_unreviewed:
        print(f"[info] Skipped {skipped_unreviewed} unreviewed verse(s). "
              f"Pass --include-unreviewed to load them anyway (testing only).")
    if skipped_no_match:
        print(f"[warn] Skipped {skipped_no_match} verse(s) with no matching raw data.")

    if not to_load:
        print("[error] Nothing to load. Did you run categorize_gita_data.py, "
              "and mark entries as reviewed?")
        sys.exit(1)

    print(f"\nReady to insert {len(to_load)} passage(s).")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            # Look up source_id and translator_id (seeded by init.sql)
            cur.execute("SELECT id FROM sources WHERE name = %s", (SOURCE_NAME,))
            row = cur.fetchone()
            if row is None:
                print(f"[error] Source '{SOURCE_NAME}' not found in sources table. "
                      f"Did init.sql run? (check docker compose logs)")
                sys.exit(1)
            source_id = row[0]

            cur.execute("SELECT id FROM translators WHERE name = %s", (TRANSLATOR_NAME,))
            row = cur.fetchone()
            if row is None:
                print(f"[error] Translator '{TRANSLATOR_NAME}' not found in translators table.")
                sys.exit(1)
            translator_id = row[0]

            # Pull tag name -> id map (seeded by init.sql)
            cur.execute("SELECT id, name FROM tags")
            tag_id_by_name = {name: tag_id for tag_id, name in cur.fetchall()}

            inserted = 0
            skipped_unknown_tags = set()
            tag_link_rows = []

            for p in to_load:
                cur.execute(
                    """
                    INSERT INTO passages
                        (source_id, chapter, verse_number, sanskrit_text,
                         transliteration, translation, translator_id,
                         summary, reviewed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id, chapter, verse_number, translator_id)
                    DO UPDATE SET
                        sanskrit_text = EXCLUDED.sanskrit_text,
                        transliteration = EXCLUDED.transliteration,
                        translation = EXCLUDED.translation,
                        summary = EXCLUDED.summary,
                        reviewed = EXCLUDED.reviewed
                    RETURNING id
                    """,
                    (
                        source_id, p["chapter"], p["verse_number"],
                        p["sanskrit_text"], p["transliteration"], p["translation"],
                        translator_id, p["summary"], p["reviewed"],
                    ),
                )
                passage_id = cur.fetchone()[0]
                inserted += 1

                for cat in p["categories"]:
                    tag_id = tag_id_by_name.get(cat)
                    if tag_id is None:
                        skipped_unknown_tags.add(cat)
                        continue
                    tag_link_rows.append((passage_id, tag_id))

            # Clear old tag links for these passages before re-inserting,
            # so re-running this script doesn't duplicate/accumulate tags
            # if a verse's categories changed after re-review.
            if tag_link_rows:
                passage_ids_touched = list({row[0] for row in tag_link_rows})
                cur.execute(
                    "DELETE FROM passage_tags WHERE passage_id = ANY(%s::uuid[])",
                    (passage_ids_touched,),
                )
                execute_values(
                    cur,
                    "INSERT INTO passage_tags (passage_id, tag_id) VALUES %s "
                    "ON CONFLICT DO NOTHING",
                    tag_link_rows,
                )

            conn.commit()
            print(f"\nInserted/updated {inserted} passage(s).")
            print(f"Inserted {len(tag_link_rows)} passage-tag link(s).")
            if skipped_unknown_tags:
                print(f"[warn] Skipped unknown tag key(s) not in tags table: "
                      f"{sorted(skipped_unknown_tags)}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\n--- Done ---")


if __name__ == "__main__":
    main()