-- ============================================================================
-- SpiritualSakha - PostgreSQL Database Schema
-- Generated for production-ready Vedic Astrology & AI Persona backend
-- ============================================================================

-- Ensure UUID generator extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ----------------------------------------------------------------------------
-- 1. USERS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'hi',
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone_number);

-- ----------------------------------------------------------------------------
-- 2. USER PROFILES TABLE (Identity, State, Occupation, Diety & Inner Feelings)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Specific Onboarding Attributes
    current_state VARCHAR(50), 
    -- Allowed values: 'Student', 'Early career', 'Building a family', 'Parenting', 'Retired', 'Between chapters'

    working_hours VARCHAR(100),
    -- Occupation / working schedule: e.g. 'Software engineer', 'teacher', 'homemaker', etc.

    deity VARCHAR(50),
    -- Primary chosen deity: 'Shiva', 'Vishnu', 'Devi', 'Ganesha', 'Krishna', 'Hanuman', 'Still discovering'

    inner_feeling VARCHAR(50),
    -- Current emotional state: 'Peaceful', 'Hopeful', 'Restless', 'Searching', 'Heavy', 'Grateful', 'Prefer not to say'

    seeking VARCHAR(50),
    -- Spiritual goal: 'Peace of Mind', 'Clarity', 'Strength', 'Healing'

    -- General spiritual context
    primary_concern VARCHAR(100) DEFAULT 'work',
    faith_level VARCHAR(50) DEFAULT 'occasional',
    tradition VARCHAR(50) DEFAULT 'hindu',
    deities JSONB DEFAULT '["shiva", "hanuman"]'::jsonb,
    current_practices JSONB DEFAULT '["prayer", "mantra"]'::jsonb,
    daily_time_minutes INT DEFAULT 10,
    life_stage VARCHAR(50) DEFAULT 'professional'
);

CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);

-- ----------------------------------------------------------------------------
-- 3. BIRTH PROFILES TABLE (DOB, Time, Place Coordinates)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS birth_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    time_of_birth TIME,
    birth_place VARCHAR(150),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    is_time_approximate BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_birth_profiles_user_id ON birth_profiles(user_id);

-- ----------------------------------------------------------------------------
-- 4. ASTROLOGY SNAPSHOTS TABLE (Swiss Ephemeris Calculations)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS astrology_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    birth_profile_id VARCHAR(36) UNIQUE NOT NULL REFERENCES birth_profiles(id) ON DELETE CASCADE,
    rashi JSONB DEFAULT '{}'::jsonb,
    nakshatra JSONB DEFAULT '{}'::jsonb,
    panchang_data JSONB DEFAULT '{}'::jsonb,
    dasha_data JSONB DEFAULT '{}'::jsonb,
    calculated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_astrology_snapshots_birth_id ON astrology_snapshots(birth_profile_id);

-- ----------------------------------------------------------------------------
-- 5. CANONICAL PERSONAS TABLE (Structured AI Context)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personas (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    persona_version VARCHAR(10) DEFAULT '1.0',
    completeness_level INT DEFAULT 0,
    canonical_json JSONB DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_personas_user_id ON personas(user_id);

-- ----------------------------------------------------------------------------
-- 6. CONVERSATIONS TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(150) DEFAULT 'Spiritual Dialogue',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);

-- ----------------------------------------------------------------------------
-- 7. MESSAGES TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- ----------------------------------------------------------------------------
-- 8. PLACES DATABASE TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS places (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    normalized_name VARCHAR(150) NOT NULL,
    state VARCHAR(100),
    country VARCHAR(100) DEFAULT 'India',
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone VARCHAR(64) DEFAULT 'Asia/Kolkata',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_places_normalized ON places(normalized_name);
