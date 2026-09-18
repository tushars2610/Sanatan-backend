-- Unified Schema for SpiritualSakha (merged scripture + app tables)
-- This file is auto-run by the postgres Docker image ONLY the first time
-- the container initializes an empty data volume. If you change this file
-- later, you'll need to run it manually or wipe the volume with
-- `docker compose down -v` and restart.

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- for gen_random_uuid()

-- =============================================
-- SCRIPTURE TABLES (Bhagavad Gita / RAG layer)
-- =============================================

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,              -- 'Bhagavad Gita', 'Isha Upanishad'
    type TEXT NOT NULL,              -- 'Gita', 'Upanishad', 'Itihasa'
    description TEXT
);

CREATE TABLE IF NOT EXISTS translators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    license_info TEXT                -- public domain / licensed / attribution required
);

CREATE TABLE IF NOT EXISTS passages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id),
    chapter TEXT,
    verse_number TEXT,                -- e.g. '2.47'
    sanskrit_text TEXT,
    transliteration TEXT,
    translation TEXT NOT NULL,
    translator_id UUID REFERENCES translators(id),
    commentary TEXT,
    story_context TEXT,               -- surrounding narrative, if any
    summary TEXT,                     -- short LLM-drafted, human-reviewed summary
    reviewed BOOLEAN NOT NULL DEFAULT false,  -- human review gate before "live"
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (source_id, chapter, verse_number, translator_id)
);

CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,        -- 'anger', 'grief', 'duty'
    cluster TEXT NOT NULL             -- 'Money', 'Mind', 'Relationships' (UI grouping)
);

CREATE TABLE IF NOT EXISTS passage_tags (
    passage_id UUID REFERENCES passages(id),
    tag_id UUID REFERENCES tags(id),
    relevance_score FLOAT DEFAULT 1.0,
    PRIMARY KEY (passage_id, tag_id)
);

CREATE TABLE IF NOT EXISTS passage_embeddings (
    passage_id UUID REFERENCES passages(id) PRIMARY KEY,
    milvus_collection TEXT NOT NULL,
    embedding_model_version TEXT NOT NULL,
    indexed_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_passage_tags_tag ON passage_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_passages_source ON passages(source_id);

-- =============================================
-- APP TABLES (users, personas, conversations)
-- =============================================

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'hi',
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    current_state VARCHAR(50),
    working_hours VARCHAR(100),
    deity VARCHAR(50),
    inner_feeling VARCHAR(50),
    seeking VARCHAR(50),
    primary_concern VARCHAR(100) DEFAULT 'work',
    faith_level VARCHAR(50) DEFAULT 'occasional',
    tradition VARCHAR(50) DEFAULT 'hindu',
    deities JSONB DEFAULT '["shiva","hanuman"]',
    current_practices JSONB DEFAULT '["prayer","mantra"]',
    daily_time_minutes INTEGER DEFAULT 10,
    life_stage VARCHAR(50) DEFAULT 'professional'
);

CREATE TABLE IF NOT EXISTS birth_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    time_of_birth TIME,
    birth_place VARCHAR(150),
    latitude FLOAT,
    longitude FLOAT,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    is_time_approximate BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS astrology_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    birth_profile_id VARCHAR(36) UNIQUE REFERENCES birth_profiles(id) ON DELETE CASCADE,
    rashi JSONB DEFAULT '{}',
    nakshatra JSONB DEFAULT '{}',
    panchang_data JSONB DEFAULT '{}',
    dasha_data JSONB DEFAULT '{}',
    calculated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS personas (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    persona_version VARCHAR(10) DEFAULT '1.0',
    completeness_level INTEGER DEFAULT 0,
    canonical_json JSONB DEFAULT '{}',
    generated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    title VARCHAR(150) DEFAULT 'Spiritual Dialogue',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);

CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,        -- 'user' | 'assistant'
    content TEXT NOT NULL,
    cited_passage_ids UUID[],         -- passages referenced in this answer
    created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);

-- =============================================
-- SEED DATA
-- =============================================

INSERT INTO tags (name, cluster) VALUES
    ('money',            'Money'),
    ('fatigue',          'Mind'),
    ('relationships',    'Relationships'),
    ('suffering',        'Mind'),
    ('overthinking',     'Mind'),
    ('fear',             'Mind'),
    ('purpose',          'Self'),
    ('duty',             'Self'),
    ('inner_peace',      'Mind'),
    ('eternal_bliss',    'Spirit'),
    ('death',            'Life'),
    ('grief',            'Life'),
    ('identity',         'Self'),
    ('desire',           'Mind'),
    ('anger',            'Mind'),
    ('detachment',       'Spirit'),
    ('personal_growth',  'Self'),
    ('doubt',            'Mind'),
    ('ego',              'Self'),
    ('faith_surrender',  'Spirit'),
    ('clarity',          'Mind'),
    ('inner_growth',     'Self'),
    ('strength',         'Self')
ON CONFLICT (name) DO NOTHING;

INSERT INTO sources (name, type, description) VALUES
    ('Bhagavad Gita', 'Gita', 'The Bhagavad Gita, 18 chapters, 700 verses.')
ON CONFLICT DO NOTHING;

INSERT INTO translators (name, license_info) VALUES
    ('Swami Sivananda', 'TODO: confirm license/attribution terms before public launch')
ON CONFLICT DO NOTHING;
