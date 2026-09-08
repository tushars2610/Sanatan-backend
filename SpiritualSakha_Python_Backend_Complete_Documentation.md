# 🕉 SpiritualSakha — Complete Python Backend & AI Persona Implementation Guide

**Document version:** 1.0  
**Date:** September 2026  
**Purpose:** Build a production-ready Python/FastAPI backend for SpiritualSakha, including authentication, user onboarding, birth-data processing, Vedic Panchang/Rashi calculation, AI persona generation, Sakha chat, daily content, and API contracts.

---

## 1. Executive Summary

SpiritualSakha is a personal spiritual companion in which a user provides identity, life-context, spiritual preferences, and optionally birth information. The backend converts this information into a **structured user profile + deterministic Vedic calculation output + AI persona JSON** that can be injected into every Sakha chatbot session.

The existing product specification describes:

- Phone + OTP authentication
- Progressive onboarding
- Panchang
- Rashi / Nakshatra
- Astro brief
- Sakha text + voice chat
- Personal shrine
- PostgreSQL
- Redis
- Gemini
- FastAPI for AI services
- Swiss Ephemeris / `pyswisseph` for astronomical calculations
- Docker deployment

The existing Panchang implementation already calculates Tithi, Vara, Nakshatra, Yoga, Karana, Moon Sign, Sun Sign, Ritu, Ayana, sunrise/sunset and optional Vimshottari Mahadasha using Swiss Ephemeris with Lahiri Ayanamsa.

For a **Python-first backend**, this document recommends consolidating the externally exposed REST API into FastAPI instead of requiring a separate Node.js API for the MVP. The same logical API contract can be retained, while Python owns authentication, profile management, astrology/Panchang computation, AI orchestration, and chat.

---

# 2. Important Source Review

The supplied project specification defines a two-service backend:

```text
Client
  ↓
Node.js/Express API
  ↓
Python FastAPI AI service
  ↓
Gemini / Panchang / Voice
```

It also defines `/api/v1/...` REST endpoints, PostgreSQL, Redis, JWT authentication, Socket.IO streaming, and a Python FastAPI AI service.

The separate Panchang project specifies Swiss Ephemeris through `pyswisseph`, Lahiri Ayanamsa, and calculations for Tithi, Vara, Nakshatra, Yoga, Karana, Rashi, Sun sign, Ritu, Ayana, sunrise/sunset and optional Vimshottari Mahadasha.

For this implementation, the recommended architecture is:

```text
Flutter / React / ESP32 / Other Client
                │
                ▼
        FastAPI /api/v1
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
 PostgreSQL   Redis    Background Jobs
     │          │          │
     └──────┬───┴──────────┘
            ▼
     Spiritual Engine
       ├─ Panchang
       ├─ Birth Chart
       ├─ Persona Builder
       ├─ Gemini Agent
       └─ Content Engine
```

This avoids duplicating authentication, validation, database access and user-profile logic across Node.js and Python.

---

# 3. Goals

## 3.1 Functional goals

The backend must:

1. Register/login users using phone + OTP.
2. Store user identity and preferences.
3. Store progressive onboarding information.
4. Accept date of birth.
5. Accept exact birth time.
6. Accept birth place.
7. Resolve birth place into latitude, longitude and timezone.
8. Calculate deterministic Vedic astronomical information.
9. Generate a canonical JSON spiritual persona.
10. Store the generated persona.
11. Regenerate the persona when relevant profile/birth data changes.
12. Provide today's Panchang.
13. Provide birth-time Panchang.
14. Provide Rashi and Nakshatra.
15. Optionally calculate Lagna and planetary placements.
16. Optionally calculate Vimshottari Dasha.
17. Provide an AI-generated personalized Sakha response.
18. Stream chat responses.
19. Persist conversations.
20. Support multilingual responses.
21. Provide daily astro/wisdom content.
22. Keep sensitive user information out of application logs.

---

# 4. Non-Goals for MVP

Do not make these mandatory in the first release:

- Full professional Jyotish consultation engine
- Guaranteed future predictions
- Medical diagnosis
- Financial/legal advice
- Automatic gemstone/yantra recommendations
- Complex horoscope matching
- Fully automated religious authority
- Human astrologer replacement

Astrology should be presented as traditional/cultural guidance rather than scientific certainty.

---

# 5. Recommended Technology Stack

| Component | Recommended |
|---|---|
| Language | Python 3.12+ |
| API | FastAPI |
| Validation | Pydantic v2 |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| Database | PostgreSQL |
| Cache | Redis |
| Background jobs | Celery + Redis |
| Astronomy | `pyswisseph` |
| Timezone | `zoneinfo` / `tzdata` |
| HTTP | `httpx` |
| AI | Gemini API |
| JWT | PyJWT |
| Password/hash utilities | `pwdlib` / Argon2 or bcrypt |
| WebSocket | FastAPI WebSocket |
| Streaming | SSE or WebSocket |
| Testing | pytest + pytest-asyncio |
| API docs | FastAPI OpenAPI |
| Container | Docker |
| Reverse proxy | Nginx/Caddy |
| Object storage | S3-compatible storage / MinIO |

---

# 6. Project Structure

Use a modular architecture rather than putting all business logic into `main.py`.

```text
spiritual_sakha/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── onboarding.py
│   │       ├── birth_profile.py
│   │       ├── astrology.py
│   │       ├── panchang.py
│   │       ├── persona.py
│   │       ├── chat.py
│   │       ├── content.py
│   │       ├── shrine.py
│   │       └── health.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   ├── constants.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── session.py
│   │   ├── base.py
│   │   └── models/
│   │       ├── user.py
│   │       ├── profile.py
│   │       ├── birth_profile.py
│   │       ├── persona.py
│   │       ├── conversation.py
│   │       ├── message.py
│   │       └── content.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── onboarding.py
│   │   ├── birth.py
│   │   ├── panchang.py
│   │   ├── astrology.py
│   │   ├── persona.py
│   │   ├── chat.py
│   │   └── content.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── otp_service.py
│   │   ├── user_service.py
│   │   ├── onboarding_service.py
│   │   ├── place_service.py
│   │   ├── panchang_service.py
│   │   ├── astrology_service.py
│   │   ├── persona_service.py
│   │   ├── sakha_agent.py
│   │   ├── conversation_service.py
│   │   ├── content_service.py
│   │   ├── quote_service.py
│   │   └── voice_service.py
│   │
│   ├── astronomy/
│   │   ├── ephemeris.py
│   │   ├── ayanamsa.py
│   │   ├── panchang.py
│   │   ├── rashi.py
│   │   ├── nakshatra.py
│   │   ├── dasha.py
│   │   └── sunrise_sunset.py
│   │
│   ├── ai/
│   │   ├── gemini_client.py
│   │   ├── prompt_builder.py
│   │   ├── persona_builder.py
│   │   ├── guardrails.py
│   │   └── context_manager.py
│   │
│   ├── workers/
│   │   ├── celery_app.py
│   │   ├── daily_content.py
│   │   └── persona_jobs.py
│   │
│   └── data/
│       ├── rashi.json
│       ├── nakshatra.json
│       ├── deity.json
│       ├── wisdom_corpus.json
│       └── places.json
│
├── migrations/
├── tests/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

# 7. Core Architectural Principle

Separate **facts/calculations** from **AI interpretation**.

This is critical.

## Deterministic layer

These should NOT be invented by Gemini:

- Birth date
- Birth time
- Birth location
- Latitude
- Longitude
- Timezone
- Moon longitude
- Sun longitude
- Rashi
- Nakshatra
- Pada
- Tithi
- Vara
- Yoga
- Karana
- Sunrise
- Sunset
- Dasha calculations

These must come from the astronomical/calculation engine.

## AI layer

Gemini may interpret:

- Personality tendencies
- Communication style
- Spiritual practice suggestions
- Daily reflection
- Contextual wisdom
- Chat responses
- Natural-language explanation

The AI must receive calculated facts as structured data.

Never ask the LLM to calculate planetary positions from memory.

---

# 8. User Data Model

A user should have three conceptual layers.

```text
User
 ├── Identity
 ├── Spiritual Profile
 ├── Birth Profile
 ├── Astrology Snapshot
 └── AI Persona
```

## 8.1 Identity

```json
{
  "name": "Amit",
  "phoneNumber": "+919876543210",
  "preferredLanguage": "hi",
  "timezone": "Asia/Kolkata"
}
```

## 8.2 Spiritual profile

```json
{
  "primaryConcern": "work",
  "faithLevel": "occasional",
  "tradition": "hindu",
  "deities": ["shiva", "hanuman"],
  "kulDevta": null,
  "guru": null,
  "currentPractices": ["prayer", "mantra"],
  "dailyTimeMinutes": 10,
  "lifeStage": "professional"
}
```

## 8.3 Birth profile

```json
{
  "dateOfBirth": "2001-10-26",
  "timeOfBirth": "13:30:00",
  "birthPlace": "Tehri Garhwal",
  "latitude": 30.375,
  "longitude": 78.480,
  "timezone": "Asia/Kolkata"
}
```

---

# 9. Birth Data Processing Pipeline

When a user supplies birth information:

```text
DOB
 │
 ▼
Validate date
 │
 ▼
Birth time
 │
 ▼
Validate time
 │
 ▼
Birth place
 │
 ├── known place → coordinates
 │
 └── unknown place → geocoding/manual confirmation
 │
 ▼
Timezone resolution
 │
 ▼
Convert local birth time → UTC
 │
 ▼
Swiss Ephemeris
 │
 ├── Sun
 ├── Moon
 ├── planets
 └── houses/Lagna if enabled
 │
 ▼
Vedic calculation layer
 │
 ├── Rashi
 ├── Nakshatra
 ├── Pada
 ├── Tithi
 ├── Vara
 ├── Yoga
 ├── Karana
 ├── Sunrise
 ├── Sunset
 └── Dasha
 │
 ▼
Astrology snapshot
 │
 ▼
Persona Builder
 │
 ▼
Canonical Persona JSON
```

---

# 10. Place Resolution

Do not store only a free-text city name.

Store:

```json
{
  "inputPlace": "Tehri Garhwal",
  "resolvedPlace": "Tehri Garhwal, Uttarakhand, India",
  "latitude": 30.375,
  "longitude": 78.480,
  "timezone": "Asia/Kolkata",
  "resolutionSource": "database"
}
```

For MVP, an offline place database is acceptable.

The existing Panchang implementation uses a small city database and supports latitude, longitude and UTC offset fallback.

For production, create a `places` table:

```sql
CREATE TABLE places (
    id UUID PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    normalized_name VARCHAR(150) NOT NULL,
    state VARCHAR(100),
    country VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_places_normalized_name
ON places(normalized_name);
```

---

# 11. Panchang Engine

The supplied Panchang project calculates:

- Tithi
- Vara
- Nakshatra
- Yoga
- Karana
- Moon Sign/Rashi
- Sun Sign
- Ritu
- Ayana
- Sunrise
- Sunset
- Optional Vimshottari Mahadasha

It uses sidereal positions with Lahiri Ayanamsa.

The backend should wrap the existing calculation code instead of duplicating calculations.

Recommended interface:

```python
class PanchangService:

    def calculate_for_datetime(
        self,
        local_datetime,
        latitude,
        longitude,
        timezone
    ) -> PanchangResult:
        ...
```

---

# 12. Canonical Panchang Response

```json
{
  "date": "2026-09-06",
  "location": {
    "name": "Gurugram",
    "latitude": 28.4595,
    "longitude": 77.0266,
    "timezone": "Asia/Kolkata"
  },
  "vara": {
    "key": "sunday",
    "name": "Ravivaar",
    "nameEn": "Sunday"
  },
  "tithi": {
    "number": 4,
    "paksha": "shukla",
    "name": "Chaturthi",
    "completionPercent": 42.4,
    "endTime": "2026-09-06T14:32:00+05:30"
  },
  "nakshatra": {
    "number": 12,
    "name": "Uttara Phalguni",
    "pada": 2,
    "ruler": "Sun",
    "endTime": "2026-09-06T18:45:00+05:30"
  },
  "yoga": {
    "number": 6,
    "name": "Siddha"
  },
  "karana": {
    "number": 8,
    "name": "Baalava"
  },
  "rashi": {
    "moon": {
      "key": "karka",
      "name": "Karka",
      "nameEn": "Cancer"
    },
    "sun": {
      "key": "simha",
      "name": "Simha",
      "nameEn": "Leo"
    }
  },
  "sunrise": "06:02:00+05:30",
  "sunset": "18:34:00+05:30",
  "moonrise": null,
  "ritu": null,
  "ayana": null
}
```

Values above are an API shape example, not authoritative astronomical values for that date/location.

---

# 13. Birth Astrology Response

Create a separate endpoint for birth calculations.

```http
POST /api/v1/astrology/birth-chart
```

Request:

```json
{
  "dateOfBirth": "2001-10-26",
  "timeOfBirth": "13:30:00",
  "birthPlace": "Tehri Garhwal",
  "latitude": 30.375,
  "longitude": 78.480,
  "timezone": "Asia/Kolkata"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "birthDetails": {},
    "rashi": {},
    "nakshatra": {},
    "panchang": {},
    "dasha": {},
    "planets": {},
    "calculation": {
      "system": "sidereal",
      "ayanamsa": "lahiri",
      "engine": "swiss_ephemeris"
    }
  },
  "meta": {
    "requestId": "uuid",
    "timestamp": "2026-09-06T10:00:00Z"
  }
}
```

---

# 14. Rashi

Canonical keys:

```text
mesh       → Aries       → Mars
vrishabh   → Taurus      → Venus
mithun     → Gemini      → Mercury
karka      → Cancer      → Moon
simha      → Leo         → Sun
kanya      → Virgo       → Mercury
tula       → Libra       → Venus
vrishchik  → Scorpio     → Mars
dhanu      → Sagittarius → Jupiter
makar      → Capricorn   → Saturn
kumbh      → Aquarius    → Saturn
meen       → Pisces      → Jupiter
```

Store both machine-readable and display forms.

```json
{
  "key": "karka",
  "name": "Karka",
  "nameEn": "Cancer",
  "nameHi": "कर्क",
  "rulingPlanet": "Moon"
}
```

---

# 15. Nakshatra

A Nakshatra object should contain:

```json
{
  "key": "uttara_phalguni",
  "name": "Uttara Phalguni",
  "nameHi": "उत्तर फाल्गुनी",
  "number": 12,
  "pada": 2,
  "ruler": "Sun"
}
```

Do not ask Gemini to infer the Nakshatra from a textual horoscope.

---

# 16. Vimshottari Dasha

The existing calculator supports optional Vimshottari Mahadasha based on Moon's Nakshatra.

Recommended response:

```json
{
  "system": "vimshottari",
  "birthMahadasha": {
    "planet": "Sun",
    "start": "2001-10-26",
    "end": "2007-01-15",
    "balanceAtBirthYears": 5.25
  },
  "sequence": [
    {
      "planet": "Sun",
      "start": "2001-10-26",
      "end": "2007-01-15"
    }
  ]
}
```

Keep the raw calculation separate from AI interpretation.

---

# 17. Persona Generation

This is the central feature.

The persona should be a **canonical JSON document**.

It must be:

- deterministic where based on facts
- versioned
- auditable
- replaceable
- safe to inject into an LLM
- independent of UI
- independent of any single model provider

---

# 18. Canonical SpiritualSakha Persona JSON

Recommended structure:

```json
{
  "personaVersion": "1.0",
  "generatedAt": "2026-09-06T10:00:00Z",

  "identity": {
    "name": "Amit",
    "preferredLanguage": "hi",
    "timezone": "Asia/Kolkata",
    "lifeStage": "professional"
  },

  "lifeContext": {
    "primaryConcern": "work",
    "faithLevel": "occasional",
    "tradition": "hindu"
  },

  "spiritualConnection": {
    "deities": ["shiva", "hanuman"],
    "kulDevta": null,
    "guru": null,
    "currentPractices": ["prayer", "mantra"],
    "dailyTimeMinutes": 10
  },

  "birth": {
    "date": "2001-10-26",
    "time": "13:30:00",
    "place": "Tehri Garhwal",
    "latitude": 30.375,
    "longitude": 78.48,
    "timezone": "Asia/Kolkata"
  },

  "vedicProfile": {
    "calculationSystem": "sidereal",
    "ayanamsa": "lahiri",

    "rashi": {
      "key": "karka",
      "name": "Karka",
      "nameEn": "Cancer",
      "nameHi": "कर्क",
      "rulingPlanet": "Moon"
    },

    "nakshatra": {
      "key": "uttara_phalguni",
      "name": "Uttara Phalguni",
      "pada": 2,
      "ruler": "Sun"
    },

    "panchangAtBirth": {
      "tithi": {},
      "vara": {},
      "yoga": {},
      "karana": {}
    },

    "dasha": {}
  },

  "persona": {
    "communicationStyle": "warm, reflective, concise",
    "preferredTone": "calm and encouraging",
    "spiritualDepth": "moderate",
    "guidanceStyle": [
      "practical",
      "compassionate",
      "question-led",
      "non-judgmental"
    ],
    "topicsToEmphasize": [
      "work-life balance",
      "discipline",
      "reflection"
    ],
    "practiceCapacityMinutes": 10
  },

  "sakhaInstructions": {
    "addressUserByName": true,
    "useDeityReferencesWhenRelevant": true,
    "avoidForcedAstrology": true,
    "language": "hi",
    "responseLength": "short"
  },

  "safety": {
    "medicalAdvice": false,
    "financialAdvice": false,
    "legalAdvice": false,
    "definitiveFuturePredictions": false,
    "fearBasedGuidance": false,
    "divineIdentityClaims": false
  }
}
```

---

# 19. Persona Generation Rules

Do NOT generate the entire persona with a single unconstrained LLM prompt.

Use a two-stage design.

## Stage A — Deterministic profile builder

Python creates:

```text
identity
lifeContext
spiritualConnection
birth
vedicProfile
```

## Stage B — AI interpretation

Gemini creates only:

```text
persona.communicationStyle
persona.preferredTone
persona.guidanceStyle
persona.topicsToEmphasize
```

Then validate the result with Pydantic.

This prevents hallucinated astrology.

---

# 20. Persona API

## Generate persona

```http
POST /api/v1/persona/generate
```

Request:

```json
{
  "includeAstrology": true,
  "includeDasha": true,
  "includeInterpretation": true
}
```

Response:

```json
{
  "success": true,
  "data": {
    "persona": {}
  },
  "meta": {
    "personaVersion": "1.0",
    "generatedAt": "2026-09-06T10:00:00Z"
  }
}
```

## Get persona

```http
GET /api/v1/persona
```

## Regenerate persona

```http
POST /api/v1/persona/regenerate
```

Regeneration should happen when:

- DOB changes
- birth time changes
- birth place changes
- rashi changes
- Nakshatra changes
- deity preferences change
- primary concern changes
- language changes
- life stage changes

---

# 21. Persona Database Table

Use versioned snapshots.

```sql
CREATE TABLE user_personas (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    version VARCHAR(20) NOT NULL,

    persona_json JSONB NOT NULL,

    source_profile_hash VARCHAR(128),
    model_used VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_personas_user
ON user_personas(user_id, created_at DESC);
```

Never overwrite the previous persona without retaining an audit/history record.

---

# 22. API Standards

All endpoints use:

```text
/api/v1/
```

Successful response:

```json
{
  "success": true,
  "data": {},
  "meta": {
    "timestamp": "2026-09-06T10:00:00Z",
    "requestId": "uuid"
  }
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid birth time",
    "details": []
  },
  "meta": {
    "timestamp": "2026-09-06T10:00:00Z",
    "requestId": "uuid"
  }
}
```

---

# 23. Complete REST API

## Authentication

```text
POST   /api/v1/auth/send-otp
POST   /api/v1/auth/verify-otp
POST   /api/v1/auth/refresh-token
POST   /api/v1/auth/logout
```

## User

```text
GET    /api/v1/user/me
PATCH  /api/v1/user/me
```

## Profile

```text
GET    /api/v1/user/profile
PATCH  /api/v1/user/profile
```

## Onboarding

```text
POST   /api/v1/user/onboarding
GET    /api/v1/user/onboarding/state
```

## Birth data

```text
GET    /api/v1/user/birth-profile
PUT    /api/v1/user/birth-profile
DELETE /api/v1/user/birth-profile
```

## Place

```text
GET    /api/v1/places/search?q=tehri
GET    /api/v1/places/{place_id}
```

## Panchang

```text
GET    /api/v1/content/panchang
POST   /api/v1/panchang/calculate
```

## Astrology

```text
POST   /api/v1/astrology/birth-chart
GET    /api/v1/astrology/profile
GET    /api/v1/astrology/dasha
```

## Persona

```text
GET    /api/v1/persona
POST   /api/v1/persona/generate
POST   /api/v1/persona/regenerate
```

## Home content

```text
GET    /api/v1/content/today
GET    /api/v1/content/astro-brief
GET    /api/v1/content/quote
```

## Chat

```text
POST   /api/v1/sakha/conversation
GET    /api/v1/sakha/conversations
GET    /api/v1/sakha/conversation/{conversation_id}
DELETE /api/v1/sakha/conversation/{conversation_id}
POST   /api/v1/sakha/chat
WS     /api/v1/sakha/ws
```

## Shrine

```text
GET    /api/v1/shrine/content
GET    /api/v1/shrine/content/{deity}
GET    /api/v1/shrine/playlist/{deity}
```

## Health

```text
GET    /api/v1/health
GET    /api/v1/health/ready
GET    /api/v1/health/live
```

---

# 24. Authentication

OTP flow:

```text
Client
 │
 ├── POST /auth/send-otp
 │
 ▼
Validate phone
 │
 ▼
Redis:
otp:{phone} = hashed OTP
TTL = 300 seconds
 │
 ▼
SMS provider
 │
 ▼
Client
 │
 └── POST /auth/verify-otp
          │
          ▼
      Verify OTP
          │
          ▼
     Create/find user
          │
          ▼
     Issue JWT
```

Recommended limits:

```text
OTP requests:
3 / phone / 10 minutes

OTP verification:
5 attempts / OTP

API:
100 requests / user / minute

Chat:
60 messages / user / hour
```

Never store plaintext OTP.

---

# 25. Profile API

PATCH request:

```json
{
  "name": "Amit",
  "preferredLanguage": "hi",
  "timezone": "Asia/Kolkata"
}
```

Profile request:

```json
{
  "primaryConcern": "work",
  "faithLevel": "occasional",
  "tradition": "hindu",
  "deities": ["shiva", "hanuman"],
  "currentPractices": ["prayer", "mantra"],
  "dailyTimeMinutes": 10,
  "lifeStage": "professional"
}
```

---

# 26. Birth Profile API

Request:

```json
{
  "dateOfBirth": "2001-10-26",
  "timeOfBirth": "13:30:00",
  "birthPlace": "Tehri Garhwal",
  "latitude": 30.375,
  "longitude": 78.480,
  "timezone": "Asia/Kolkata"
}
```

Validation:

- Date must be valid.
- Time must be valid.
- Latitude must be between -90 and +90.
- Longitude must be between -180 and +180.
- Timezone must be a valid IANA timezone.
- Birth place should be resolved/confirmed.
- If time is unknown, explicitly mark it as unknown.
- Never silently invent birth time.

---

# 27. Onboarding API

The existing onboarding design is progressive:

```text
1. Welcome
2. Current concern
3. Immediate value
4. Permission to personalize
5. Faith/tradition
6. Deity
7. Practices/time
8. Shrine
```

The backend endpoint:

```http
POST /api/v1/user/onboarding
```

Example:

```json
{
  "step": 2,
  "data": {
    "primaryConcern": "work"
  }
}
```

Another:

```json
{
  "step": 6,
  "data": {
    "deities": ["shiva", "hanuman"],
    "hasKulDevta": false
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "currentStep": 7,
    "profileCompleteness": 45
  }
}
```

The client should be allowed to send only fields valid for that step.

---

# 28. Today's Content API

```http
GET /api/v1/content/today
```

Response:

```json
{
  "success": true,
  "data": {
    "panchang": {},
    "astroBrief": {},
    "quote": {
      "text": "...",
      "source": "Bhagavad Gita 2.47",
      "context": "..."
    }
  }
}
```

Use DB/Redis cache.

Do not calculate Panchang from scratch on every home-screen request.

---

# 29. Chat Architecture

Recommended Python-first architecture:

```text
Client
  │
  │ WebSocket
  ▼
FastAPI
  │
  ├── Authenticate JWT
  ├── Save user message
  ├── Load persona
  ├── Load recent conversation
  ├── Build prompt
  │
  ▼
Sakha Agent
  │
  ▼
Gemini streaming
  │
  ├── token
  ├── token
  ├── token
  └── complete
  │
  ▼
FastAPI WebSocket
  │
  ▼
Client
```

---

# 30. Chat Request

```json
{
  "conversationId": "uuid",
  "content": "I am feeling confused about my career.",
  "contentType": "text"
}
```

Server should:

1. Authenticate.
2. Verify conversation ownership.
3. Persist user message.
4. Retrieve persona.
5. Retrieve last 20 messages.
6. Retrieve summary of older conversation.
7. Build system prompt.
8. Call Gemini.
9. Stream output.
10. Save final assistant message.
11. Return completion event.

---

# 31. WebSocket Events

Client:

```json
{
  "event": "sakha:message",
  "data": {
    "conversationId": "uuid",
    "content": "I am confused about my career.",
    "contentType": "text"
  }
}
```

Server:

```json
{
  "event": "sakha:typing",
  "data": {
    "conversationId": "uuid"
  }
}
```

Streaming:

```json
{
  "event": "sakha:response",
  "data": {
    "conversationId": "uuid",
    "token": "Namaste"
  }
}
```

Completion:

```json
{
  "event": "sakha:response:end",
  "data": {
    "conversationId": "uuid",
    "messageId": "uuid",
    "fullContent": "..."
  }
}
```

Error:

```json
{
  "event": "sakha:error",
  "data": {
    "conversationId": "uuid",
    "code": "AI_GENERATION_FAILED",
    "message": "Unable to generate response."
  }
}
```

---

# 32. Gemini Prompt Architecture

Do not concatenate everything into one giant string manually.

Use layers:

```text
SYSTEM RULES
      +
SAKHA PERSONA
      +
USER PERSONA JSON
      +
RELEVANT ASTRO DATA
      +
CONVERSATION SUMMARY
      +
LAST 20 MESSAGES
      +
CURRENT USER MESSAGE
```

Example:

```text
SYSTEM
You are Sakha...

PERSONA
{
  "identity": {...},
  "spiritualConnection": {...},
  "vedicProfile": {...},
  "persona": {...},
  "safety": {...}
}

CONVERSATION SUMMARY
...

RECENT MESSAGES
...

USER
I am feeling confused about my career.
```

---

# 33. AI Persona Injection

Only include populated fields.

Bad:

```text
Deity: null
Guru: null
Life stage: null
```

Better:

```text
The user is connected with Shiva and Hanuman.
The user practices mantra and prayer.
The user currently has a work-related concern.
```

The AI should use context naturally and should not mention astrology in every answer.

---

# 34. Sakha System Rules

Sakha should:

- Be warm.
- Be patient.
- Speak simply.
- Avoid lecturing.
- Ask reflective questions.
- Give practical suggestions.
- Adapt to language preference.
- Use the user's name naturally.
- Reference spiritual preferences only when relevant.
- Treat astrology as traditional wisdom.
- Admit uncertainty.

Sakha must never:

- Claim to be divine.
- Claim to be a deity.
- Claim to be a guru.
- Give medical treatment.
- Give definitive legal/financial advice.
- Make certain predictions about the future.
- Use fear or superstition to manipulate.
- Disparage another faith/tradition.
- Claim a gemstone/puja will definitely solve a problem.

---

# 35. Conversation Context

For normal chat:

```text
System prompt
+
Persona JSON
+
Conversation summary
+
Last 20 messages
+
Current message
```

For conversations exceeding the context policy:

```text
Old messages
   ↓
Summarizer
   ↓
Conversation summary
   ↓
Recent messages
```

Example summary:

```json
{
  "summaryVersion": 1,
  "importantTopics": [
    "career uncertainty",
    "relationship with father"
  ],
  "userPreferences": [
    "prefers practical suggestions"
  ],
  "unresolvedQuestions": [
    "whether to change jobs"
  ]
}
```

---

# 36. Database Design

Core tables:

```text
users
user_profiles
birth_profiles
astrology_snapshots
user_personas
refresh_tokens
conversations
chat_messages
conversation_summaries
daily_content
shrine_content
places
```

Recommended relationships:

```text
users
 ├── user_profiles          1:1
 ├── birth_profiles         1:1
 ├── astrology_snapshots    1:N
 ├── user_personas          1:N
 ├── conversations          1:N
 └── refresh_tokens         1:N

conversations
 ├── chat_messages          1:N
 └── conversation_summary   1:1/current
```

---

# 37. Astrology Snapshot Table

```sql
CREATE TABLE astrology_snapshots (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    calculation_system VARCHAR(30) NOT NULL,
    ayanamsa VARCHAR(50) NOT NULL,

    rashi JSONB,
    nakshatra JSONB,
    panchang JSONB,
    planets JSONB,
    lagna JSONB,
    dasha JSONB,

    input_hash VARCHAR(128) NOT NULL,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_astrology_snapshots_user
ON astrology_snapshots(user_id, created_at DESC);
```

Use `input_hash` to prevent unnecessary recalculation.

---

# 38. Caching Strategy

Redis keys:

```text
otp:{phone}
otp_attempts:{phone}

panchang:{date}:{lat}:{lon}:{timezone}

place:{normalized_name}

persona:{user_id}:{profile_hash}

rate_limit:{user_id}

conversation_summary:{conversation_id}
```

Panchang is highly cacheable.

Persona is cacheable until relevant user information changes.

---

# 39. Background Jobs

Use Celery.

Jobs:

```text
generate_daily_panchang
generate_daily_astro_briefs
generate_daily_quote
generate_persona
summarize_conversation
cleanup_expired_sessions
```

Daily content:

```text
00:05 IST
   │
   ├── Panchang
   ├── 12 Rashi briefs
   └── Wisdom quote
```

For location-specific Panchang, do not assume one global Panchang for every user. Cache by date + location/timezone.

---

# 40. Daily Content Schema

```json
{
  "contentDate": "2026-09-06",
  "panchang": {},
  "astroBriefs": {
    "mesh": {},
    "vrishabh": {},
    "mithun": {},
    "karka": {},
    "simha": {},
    "kanya": {},
    "tula": {},
    "vrishchik": {},
    "dhanu": {},
    "makar": {},
    "kumbh": {},
    "meen": {}
  },
  "quote": {
    "text": "...",
    "source": "...",
    "context": "..."
  }
}
```

---

# 41. Suggested SQL Tables

## users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    phone_verified BOOLEAN DEFAULT FALSE,
    name VARCHAR(100),
    preferred_language VARCHAR(20) DEFAULT 'en',
    timezone VARCHAR(64) DEFAULT 'Asia/Kolkata',
    onboarding_step INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## user_profiles

```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    primary_concern VARCHAR(50),
    faith_level VARCHAR(50),
    tradition VARCHAR(50),

    deities TEXT[],
    has_kul_devta BOOLEAN DEFAULT FALSE,
    kul_devta_name VARCHAR(100),
    guru_name VARCHAR(100),

    current_practices TEXT[],
    daily_time_minutes INTEGER,

    life_stage VARCHAR(50),
    personalisation_opted BOOLEAN DEFAULT FALSE,
    shrine_created BOOLEAN DEFAULT FALSE,

    profile_completeness INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## birth_profiles

```sql
CREATE TABLE birth_profiles (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    date_of_birth DATE NOT NULL,
    time_of_birth TIME,
    birth_place VARCHAR(150) NOT NULL,

    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    timezone VARCHAR(64),

    place_resolution_status VARCHAR(30) DEFAULT 'pending',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

# 42. Security

This application handles sensitive personal information.

Never log:

```text
DOB
birth time
birth place
latitude/longitude linked to user
rashi
nakshatra
gotra
deity preferences
chat contents
persona JSON
OTP
JWT
```

Use:

```text
user_id
request_id
endpoint
status
latency
error_code
```

instead.

JWT:

```text
Access token: short-lived
Refresh token: long-lived
Refresh token stored hashed
```

Never store refresh tokens in plaintext in PostgreSQL.

---

# 43. Privacy

Users should be able to:

```text
View profile
Edit profile
Edit birth data
Regenerate persona
Delete conversations
Delete persona
Delete account
Export personal data
```

Account deletion must cascade or anonymize dependent data according to the product's retention policy.

---

# 44. API Validation

Use Pydantic.

Example:

```python
class BirthProfileRequest(BaseModel):
    date_of_birth: date
    time_of_birth: time | None = None
    birth_place: str = Field(min_length=2, max_length=150)

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    timezone: str | None = None
```

Use validators for:

- future DOB
- impossible dates
- invalid timezone
- invalid coordinates
- malformed phone
- unsupported language
- unsupported onboarding values

---

# 45. API Error Codes

Use stable machine-readable codes.

```text
VALIDATION_ERROR
UNAUTHORIZED
FORBIDDEN
NOT_FOUND
OTP_EXPIRED
OTP_INVALID
OTP_RATE_LIMITED
BIRTH_DATA_INVALID
PLACE_NOT_RESOLVED
ASTROLOGY_CALCULATION_FAILED
PERSONA_GENERATION_FAILED
AI_GENERATION_FAILED
CONVERSATION_NOT_FOUND
RATE_LIMITED
INTERNAL_ERROR
```

---

# 46. Important Panchang Caveats

The supplied Panchang implementation notes:

1. Calculations use sidereal Lahiri positions.
2. Western tropical astrology differs from this system.
3. Vara is currently based on civil calendar date rather than sunrise-to-sunrise Vedic day.
4. Lagna and detailed house placements are not included in that version.
5. Important dates should be cross-checked against professional/dedicated Panchang authorities.

These limitations should be documented in the API and product wherever relevant.

---

# 47. Do Not Mix Panchang and Birth Chart

They are related but not identical.

Use:

```text
Panchang
→ date/location/day calculation

Birth Chart
→ exact birth date/time/location

Persona
→ user profile + birth chart + spiritual preferences + AI interpretation
```

For example:

```text
GET /content/panchang
```

should answer:

> What is today's Tithi?

Whereas:

```text
POST /astrology/birth-chart
```

should answer:

> What was the Moon's sidereal position when this person was born?

---

# 48. Persona Versioning

Every persona must contain:

```json
{
  "personaVersion": "1.0"
}
```

If the schema changes:

```text
1.0 → initial schema
1.1 → additive fields
2.0 → breaking structure change
```

Store the version in PostgreSQL.

This allows future AI agents to understand which persona format they are receiving.

---

# 49. Model Independence

Do not build persona JSON around Gemini-specific concepts.

Bad:

```json
{
  "geminiPrompt": "..."
}
```

Good:

```json
{
  "persona": {},
  "sakhaInstructions": {},
  "safety": {}
}
```

Then create:

```text
Persona JSON
     ↓
Prompt Adapter
     ├── Gemini
     ├── another LLM
     └── future model
```

---

# 50. Prompt Builder Interface

Recommended:

```python
class PromptBuilder:

    def build_system_prompt(
        self,
        persona: dict,
        conversation_summary: str | None,
        recent_messages: list,
        user_message: str
    ) -> str:
        ...
```

Do not put database calls inside the prompt builder.

---

# 51. Persona Builder Interface

```python
class PersonaBuilder:

    async def build(
        self,
        user,
        profile,
        birth_profile,
        astrology_snapshot
    ) -> dict:
        ...
```

Process:

```text
User
 ↓
Profile
 ↓
Birth Profile
 ↓
Astrology Snapshot
 ↓
Deterministic Persona
 ↓
Optional AI interpretation
 ↓
Pydantic validation
 ↓
PostgreSQL JSONB
```

---

# 52. Testing Strategy

## Unit tests

Test:

```text
Rashi boundaries
Nakshatra boundaries
Tithi calculation
Yoga calculation
Karana calculation
Dasha calculation
Timezone conversion
Sunrise/sunset
Place resolution
Persona schema
```

## API tests

Test:

```text
OTP
Auth
Profile
Onboarding
Birth profile
Panchang
Birth chart
Persona
Chat
```

## AI tests

Test:

```text
Persona injection
Language adaptation
Guardrails
No divine claims
No definitive prediction
No medical advice
No religious disparagement
```

---

# 53. Golden Astrology Test Cases

Create a fixed test dataset:

```json
[
  {
    "name": "Test User 1",
    "date": "2001-10-26",
    "time": "13:30:00",
    "place": "Tehri Garhwal"
  },
  {
    "name": "Test User 2",
    "date": "1999-04-01",
    "time": "04:00:00",
    "place": "Dhanbad"
  }
]
```

Run these after every change to the astronomical engine.

The expected output should be versioned.

This prevents accidental changes to astrology calculations during refactoring.

---

# 54. API Documentation

FastAPI automatically exposes:

```text
/docs
/redoc
/openapi.json
```

Add descriptions and examples to every Pydantic model.

The API documentation should clearly identify:

```text
Input
Validation
Output
Errors
Authentication
Rate limits
```

---

# 55. Environment Variables

```env
APP_ENV=development
APP_NAME=SpiritualSakha
APP_VERSION=1.0.0

DATABASE_URL=postgresql+asyncpg://sakha:password@postgres:5432/spiritualsakha
REDIS_URL=redis://redis:6379/0

JWT_SECRET=replace-with-strong-secret
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=30

GEMINI_API_KEY=replace-me
GEMINI_MODEL=replace-me

SMS_PROVIDER_API_KEY=replace-me

GOOGLE_CLOUD_PROJECT_ID=replace-me
GOOGLE_APPLICATION_CREDENTIALS=/secrets/google-service-account.json

S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=replace-me
S3_SECRET_KEY=replace-me
S3_BUCKET=sakha-media

DEFAULT_TIMEZONE=Asia/Kolkata
ASTROLOGY_AYANAMSA=LAHIRI
```

Never commit `.env`.

---

# 56. Requirements

Example:

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings

sqlalchemy
asyncpg
alembic

redis
celery

httpx

pyswisseph

PyJWT
pwdlib[argon2]

python-multipart

pytest
pytest-asyncio
```

Add the exact Gemini SDK package/version selected by the implementation team after confirming the current provider SDK.

---

# 57. Docker

Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

# 58. Docker Compose

```yaml
services:

  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=INFO
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  beat:
    build: .
    command: celery -A app.workers.celery_app beat --loglevel=INFO
    env_file:
      - .env
    depends_on:
      - redis

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: spiritualsakha
      POSTGRES_USER: sakha
      POSTGRES_PASSWORD: change-me
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

---

# 59. Deployment

Recommended MVP:

```text
Hostinger KVM
│
├── Docker
│
├── FastAPI
├── Celery Worker
├── Celery Beat
├── PostgreSQL
└── Redis
```

For production, database backups should be separate from the application container lifecycle.

Use:

```text
HTTPS
Firewall
SSH keys
Secrets outside Git
PostgreSQL backups
Redis authentication where appropriate
Non-root containers
Health checks
Automatic restart
```

---

# 60. Recommended Development Sequence

Do NOT ask an AI coding agent to build everything in one pass.

Build in vertical slices.

## Phase 1 — Foundation

```text
FastAPI
PostgreSQL
Redis
Alembic
Docker
Config
Health endpoints
```

## Phase 2 — Authentication

```text
send OTP
verify OTP
JWT
refresh
logout
```

## Phase 3 — User profile

```text
user
profile
onboarding
```

## Phase 4 — Birth profile

```text
birth data
place resolution
timezone
validation
```

## Phase 5 — Panchang

```text
Swiss Ephemeris
Panchang service
Rashi
Nakshatra
Tithi
Yoga
Karana
Sunrise/sunset
Dasha
```

## Phase 6 — Persona

```text
Astrology snapshot
Persona schema
Persona builder
Persona storage
Persona API
```

## Phase 7 — AI

```text
Gemini client
Prompt builder
Conversation context
Streaming
Guardrails
```

## Phase 8 — Content

```text
daily Panchang
rashi briefs
wisdom quotes
cache
Celery
```

## Phase 9 — Production

```text
logging
rate limits
monitoring
backups
security
load tests
```

---

# 61. Suggested Git Branches

```text
main
develop

feature/SS-001-fastapi-foundation
feature/SS-002-auth
feature/SS-003-user-profile
feature/SS-004-birth-profile
feature/SS-005-panchang
feature/SS-006-astrology
feature/SS-007-persona
feature/SS-008-sakha-chat
feature/SS-009-daily-content
feature/SS-010-production
```

Commit style:

```text
feat(auth): implement otp verification
feat(astro): add sidereal rashi calculation
feat(persona): add persona generation
fix(panchang): correct timezone conversion
test(astro): add nakshatra boundary tests
```

---

# 62. Coding Rules for AI Coding Agents

When giving this repository to Claude, Cursor, Antigravity or another coding agent, enforce:

1. Read the entire repository before changing architecture.
2. Never invent existing files.
3. Never silently change API contracts.
4. Never replace Swiss Ephemeris calculations with LLM reasoning.
5. Never store secrets in source code.
6. Use Pydantic models for all external requests/responses.
7. Use async database access consistently.
8. Use migrations for schema changes.
9. Add tests with every business-logic feature.
10. Do not modify existing calculation formulas without regression tests.
11. Keep astronomy, AI, database and HTTP layers separated.
12. Never expose internal stack traces to clients.
13. Never log sensitive birth/spiritual/chat data.
14. Keep response JSON backwards-compatible where possible.
15. Do not make a breaking change without updating API documentation.
16. Do not allow one user to access another user's conversation/persona.
17. Always validate conversation ownership.
18. Use idempotency where background persona generation can be retried.
19. Use timezones explicitly; never rely on server local time.
20. Treat AI-generated text as untrusted output and validate structured responses.

---

# 63. Critical AI-Agent Instruction

The coding agent must understand this rule:

> **Astronomical facts are software output, not AI output.**

For example:

```text
User DOB + Time + Place
       ↓
Python + Swiss Ephemeris
       ↓
Moon longitude
       ↓
Rashi
       ↓
Nakshatra
       ↓
Panchang
       ↓
Persona JSON
       ↓
Gemini
       ↓
Natural-language interpretation
```

Never:

```text
User DOB
  ↓
Gemini
  ↓
"Your Rashi is probably..."
```

---

# 64. Recommended API Dependency Flow

```text
/auth
   │
   ▼
/user
   │
   ▼
/birth-profile
   │
   ▼
/astrology/birth-chart
   │
   ▼
/persona
   │
   ▼
/sakha/chat
```

A user should not be required to have a complete astrology profile to use Sakha.

The system should gracefully support:

```text
No birth data
     ↓
Generic spiritual persona

Partial birth data
     ↓
Partial persona

Complete birth data
     ↓
Full Vedic profile
```

---

# 65. Persona Completeness Levels

Implement:

```text
LEVEL_0
No profile

LEVEL_1
Name/language

LEVEL_2
Spiritual preferences

LEVEL_3
DOB

LEVEL_4
DOB + birth place

LEVEL_5
DOB + exact birth time + place

LEVEL_6
Full personalization + astrology + practices
```

This lets Sakha remain useful without forcing users to provide sensitive information.

---

# 66. API Example — Complete Persona Generation

Request:

```http
POST /api/v1/persona/generate
Authorization: Bearer <token>
Content-Type: application/json
```

Response:

```json
{
  "success": true,
  "data": {
    "persona": {
      "personaVersion": "1.0",
      "identity": {
        "name": "Amit",
        "preferredLanguage": "hi"
      },
      "lifeContext": {
        "primaryConcern": "work"
      },
      "spiritualConnection": {
        "deities": ["shiva"],
        "currentPractices": ["mantra"],
        "dailyTimeMinutes": 10
      },
      "birth": {
        "date": "2001-10-26",
        "time": "13:30:00",
        "place": "Tehri Garhwal"
      },
      "vedicProfile": {
        "rashi": {},
        "nakshatra": {},
        "panchangAtBirth": {},
        "dasha": {}
      },
      "persona": {
        "communicationStyle": "warm and reflective",
        "guidanceStyle": [
          "practical",
          "compassionate"
        ]
      },
      "safety": {
        "definitiveFuturePredictions": false,
        "medicalAdvice": false
      }
    }
  },
  "meta": {
    "personaVersion": "1.0"
  }
}
```

---

# 67. What Should Be Stored vs Calculated

## Store

```text
User identity
Profile
Birth input
Resolved coordinates
Timezone
Astrology snapshot
Persona snapshot
Chat messages
Conversation summaries
Daily generated content
```

## Calculate/cache

```text
Rashi
Nakshatra
Tithi
Yoga
Karana
Sunrise
Sunset
Dasha
```

## Generate with AI

```text
Communication style
Guidance style
Daily interpretation
Astro brief
Wisdom context
Chat response
```

---

# 68. API Review — Existing Contract vs Recommended Python Contract

The supplied specification already has a good foundation:

```text
/api/v1/auth/*
/api/v1/user/*
/api/v1/content/*
/api/v1/sakha/*
/api/v1/shrine/*
```

Keep those paths for client compatibility.

Add:

```text
/api/v1/user/birth-profile
/api/v1/astrology/birth-chart
/api/v1/astrology/profile
/api/v1/astrology/dasha
/api/v1/persona
/api/v1/persona/generate
/api/v1/persona/regenerate
/api/v1/places/search
```

The biggest architectural improvement is to make the Python service the authoritative backend if Python is the team's primary backend language.

If Node.js is retained later, keep the boundary:

```text
Node API
   ↓
Python internal API
```

but do not duplicate business rules in both services.

---

# 69. Production Readiness Checklist

## Backend

- [ ] FastAPI
- [ ] PostgreSQL
- [ ] Redis
- [ ] Alembic
- [ ] JWT
- [ ] OTP
- [ ] Rate limits
- [ ] Pydantic validation
- [ ] Structured errors
- [ ] OpenAPI
- [ ] Health checks

## Astrology

- [ ] Swiss Ephemeris
- [ ] Lahiri Ayanamsa
- [ ] Explicit timezone conversion
- [ ] Rashi
- [ ] Nakshatra
- [ ] Pada
- [ ] Tithi
- [ ] Vara
- [ ] Yoga
- [ ] Karana
- [ ] Sunrise/sunset
- [ ] Dasha
- [ ] Regression test dataset

## Persona

- [ ] Canonical JSON schema
- [ ] Pydantic validation
- [ ] Persona version
- [ ] Source profile hash
- [ ] Snapshot storage
- [ ] Regeneration endpoint
- [ ] No hallucinated astronomical facts

## AI

- [ ] Gemini adapter
- [ ] Prompt builder
- [ ] Persona injection
- [ ] Conversation summary
- [ ] Last-message window
- [ ] Streaming
- [ ] Guardrails
- [ ] AI output validation

## Security

- [ ] No sensitive logs
- [ ] HTTPS
- [ ] Secret management
- [ ] JWT rotation/revocation
- [ ] Conversation ownership
- [ ] Rate limiting
- [ ] DB backups
- [ ] Account deletion

---

# 70. Final Recommended Architecture

```mermaid
flowchart TD

    A[Flutter / React / Client] --> B[FastAPI]

    B --> C[Auth Service]
    B --> D[User/Profile Service]
    B --> E[Birth Profile Service]
    B --> F[Panchang Service]
    B --> G[Astrology Service]
    B --> H[Persona Service]
    B --> I[Sakha Agent]
    B --> J[Content Service]

    C --> K[(PostgreSQL)]
    D --> K
    E --> K
    H --> K
    I --> K
    J --> K

    B --> L[(Redis)]
    J --> M[Celery]
    M --> F
    M --> J

    F --> N[Swiss Ephemeris]
    G --> N

    H --> I
    I --> O[Gemini]

    J --> P[Wisdom Corpus]
    J --> Q[Rashi Data]
```

---

# 71. End-to-End User Journey

```text
User installs app
      ↓
Phone + OTP
      ↓
Basic onboarding
      ↓
Name / language / concern
      ↓
Spiritual preferences
      ↓
Optional DOB + birth time + birth place
      ↓
Place resolution
      ↓
Timezone resolution
      ↓
Swiss Ephemeris
      ↓
Rashi + Nakshatra + Panchang + Dasha
      ↓
Astrology Snapshot
      ↓
Persona Builder
      ↓
Canonical Persona JSON
      ↓
Store Persona Snapshot
      ↓
Sakha Chat
      ↓
Persona + Context + User Message
      ↓
Gemini
      ↓
Streaming Response
```

---

# 72. The Most Important Design Decision

The **Persona JSON is the contract between the product profile system and the AI agent**.

Therefore:

```text
Database schema
       ↓
Domain models
       ↓
Astrology engine
       ↓
Persona JSON
       ↓
AI prompt adapter
       ↓
LLM
```

Do not make the frontend responsible for constructing the AI persona.

The frontend should only collect/display information.

The backend must own:

```text
validation
calculation
normalization
persona generation
security
persistence
AI context
```

---

# 73. First Milestone for an AI Coding Agent

The first implementation milestone should produce a running backend with:

```text
GET  /api/v1/health
POST /api/v1/auth/send-otp
POST /api/v1/auth/verify-otp

GET   /api/v1/user/me
PATCH /api/v1/user/me

GET   /api/v1/user/profile
PATCH /api/v1/user/profile

PUT /api/v1/user/birth-profile
GET /api/v1/user/birth-profile

POST /api/v1/astrology/birth-chart

GET  /api/v1/persona
POST /api/v1/persona/generate

GET /api/v1/content/panchang
GET /api/v1/content/today

POST /api/v1/sakha/conversation
GET  /api/v1/sakha/conversations
GET  /api/v1/sakha/conversation/{id}
POST /api/v1/sakha/chat
WS   /api/v1/sakha/ws
```

The implementation should include:

```text
Docker
PostgreSQL
Redis
Alembic
Pydantic models
SQLAlchemy models
Swiss Ephemeris adapter
Persona schema
Tests
OpenAPI
```

Do not implement the entire mobile/web frontend before these contracts are stable.

---

# 74. Reference Material Used

This implementation guide is based primarily on the supplied SpiritualSakha MVP developer specification and the supplied Panchang Calculator README.

The supplied specification defines the product, architecture, API conventions, database models, onboarding, AI agent rules, daily content, deployment and sprint plan.

The supplied Panchang README defines the existing astronomical engine and its supported calculations.

---

# 75. Final Rule for the Project

> **SpiritualSakha should be a deterministic spiritual-data platform with an AI interpretation layer — not an AI model pretending to be an astrology calculator.**

The calculation engine produces the facts.

The persona builder converts facts + user preferences into structured context.

The AI turns that context into a warm conversational experience.

That separation will make the system easier to test, safer, easier to replace with another LLM, and much easier for Claude, Antigravity or another coding agent to implement correctly.