"""
chat_service.py

Full RAG-grounded spiritual chat pipeline for Sakha.

Flow for every message:
  1. RagService.search() — retrieve top-5 Gita passages from Milvus + Postgres
  2. Build a rich spiritual system prompt with:
       - Character rules for Sakha's persona
       - User's canonical persona (name, deity, concern, Vedic profile, AI insights)
       - Retrieved scripture passages as grounded context
  3. Call Gemini to generate a warm, cited, spiritually-grounded reply
  4. Return the reply text + list of cited passage IDs for storage
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

import httpx

from app.core.config import get_settings
from app.services.rag_service import RagService, RetrievedPassage

settings = get_settings()

# Singleton RAG service — model loaded once at startup
_rag = RagService(milvus_host=settings.MILVUS_HOST, milvus_port=settings.MILVUS_PORT)

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "can't go on",
    "want to die", "no reason to live", "harm myself",
    "जीना नहीं", "मर जाना", "खुद को नुकसान",
]


def _detect_crisis(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in CRISIS_KEYWORDS)


def _build_system_prompt(
    persona_json: Dict[str, Any],
    passages: List[RetrievedPassage],
) -> str:
    # ── Identity ──────────────────────────────────────────────────────────────
    identity = persona_json.get("identity", {})
    name = identity.get("name", "Friend")
    lang = identity.get("preferredLanguage", "hi")
    life_stage = identity.get("lifeStage", "")

    # ── Life context ──────────────────────────────────────────────────────────
    life = persona_json.get("lifeContext", {})
    concern = life.get("primaryConcern", "life")
    faith = life.get("faithLevel", "")
    tradition = life.get("tradition", "Hindu")

    # ── Spiritual connection ───────────────────────────────────────────────────
    spirit = persona_json.get("spiritualConnection", {})
    deities = spirit.get("deities", ["the Divine"])
    practices = spirit.get("currentPractices", [])

    # ── AI Insights (Sakha persona style) ─────────────────────────────────────
    insights = persona_json.get("ai_insights", persona_json.get("aiInsights", {}))
    sakha = insights.get("sakha_persona", insights.get("sakhaPersona", {}))
    comm_style = sakha.get("communication_style", sakha.get("communicationStyle", "warm and concise"))
    tone = sakha.get("preferred_tone", sakha.get("preferredTone", "calm"))
    guidance_styles = sakha.get("guidance_style", sakha.get("guidanceStyle", ["practical"]))
    topics = sakha.get("topics_to_emphasize", sakha.get("topicsToEmphasize", []))
    daily_habits = insights.get("recommended_daily_habits", insights.get("recommendedDailyHabits", []))
    
    # Deity specific practices
    deity_practices_list = insights.get("deity_practices", insights.get("deityPractices", []))
    deity_practices_str = ""
    if deity_practices_list:
        dp = deity_practices_list[0]
        deity_practices_str = f"Mantra: {dp.get('suggested_mantra', '')}\nPuja: {dp.get('puja_routine', '')}"

    # Astrological insights
    astro_traits = insights.get("astrological_traits", insights.get("astrologicalTraits", {}))
    karmic_focus = astro_traits.get("karmic_focus", astro_traits.get("karmicFocus", ""))
    strengths = astro_traits.get("strengths", [])

    # ── Vedic profile ──────────────────────────────────────────────────────────
    vedic = persona_json.get("vedic_profile", persona_json.get("vedicProfile", {}))
    rashi = vedic.get("rashi_name", vedic.get("rashiName", ""))
    nakshatra = vedic.get("nakshatra_name", vedic.get("nakshatraName", ""))

    # ── Character section ──────────────────────────────────────────────────────
    prompt = f"""\
You are Sakha — a deeply wise, warm, and non-judgmental spiritual companion rooted in the \
Sanatana Dharma tradition. You speak with the patience of a lifelong friend and the depth \
of a Vedic scholar.

═══ USER PERSONA ══════════════════════════════════════════════════════════════
Name            : {name}
Life Stage      : {life_stage}
Primary Concern : {concern}
Faith Level     : {faith}  |  Tradition: {tradition}
Deities         : {", ".join(deities)}
Practices       : {", ".join(practices) if practices else "reflection"}
Vedic Profile   : Rashi — {rashi or "unknown"}, Nakshatra — {nakshatra or "unknown"}
Astrology Focus : {karmic_focus or 'unknown'}
Strengths       : {", ".join(strengths) if strengths else 'unknown'}

Deity Practices for {name}:
{deity_practices_str}

Your Communication Style for {name}:
  • Tone           : {tone}
  • Style          : {comm_style}
  • Guidance modes : {", ".join(guidance_styles)}
  • Topics to weave: {", ".join(topics) if topics else "inner peace, duty, surrender"}
  • Suggested daily habits you may mention: {", ".join(daily_habits) if daily_habits else "morning silence, gratitude"}
═══════════════════════════════════════════════════════════════════════════════

═══ RETRIEVED SCRIPTURE (ground every answer here) ════════════════════════════
"""

    if passages:
        for i, p in enumerate(passages, 1):
            prompt += f"\n{i}. {p.citation_block}\n"
    else:
        prompt += "(No passages retrieved — speak from general Vedic wisdom, but be honest that you are not quoting directly.)\n"

    prompt += """\
═══════════════════════════════════════════════════════════════════════════════

═══ STRICT RULES ══════════════════════════════════════════════════════════════
1. ALWAYS anchor your answer in the scripture passages above. Cite them inline \
   as (Bhagavad Gita X.Y) — never fabricate a verse reference.
2. If no passage perfectly fits, say so honestly and offer related wisdom.
3. Never claim to be a deity, guru, or divine entity yourself.
4. Do NOT give medical, financial, or legal advice.
5. Do NOT make definitive predictions about the future.
6. Be concise — 3 to 5 warm, reflective paragraphs maximum.
7. Close every reply with a single gentle, practical suggestion {name} can \
   apply today.
8. Respond primarily in the same language {name} used; switch naturally \
   between Hindi/Hinglish/English as they do.
"""
    return prompt


class ChatService:
    @classmethod
    async def generate_response(
        cls,
        user_message: str,
        persona_json: Dict[str, Any],
        recent_messages: List[Dict[str, str]],
    ) -> Tuple[str, List[str]]:
        """
        Returns (reply_text, cited_passage_ids).
        """
        # ── Crisis check ───────────────────────────────────────────────────────
        if _detect_crisis(user_message):
            crisis_reply = (
                "I hear your pain, and I am here with you. Please know you are not alone. "
                "Your life is precious. I gently urge you to reach out to iCall India "
                "(9152987821) or a trusted person near you right now. "
                "The Gita reminds us: *nainaṁ chindanti śastrāṇi* — the soul is eternal and indestructible. "
                "You matter deeply."
            )
            return crisis_reply, []

        # ── RAG search ─────────────────────────────────────────────────────────
        passages: List[RetrievedPassage] = []
        try:
            passages = await _rag.search(user_message, top_k=5)
        except Exception as e:
            print(f"[RagService] search failed: {e} — proceeding without RAG")

        cited_ids = [p.passage_id for p in passages]

        # ── Build LLM payload ──────────────────────────────────────────────────
        system_prompt = _build_system_prompt(persona_json, passages)

        contents = []
        for msg in recent_messages[-10:]:
            contents.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": msg["content"]}],
            })
        contents.append({"role": "user", "parts": [{"text": user_message}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": 0.65,
                "maxOutputTokens": 600,
            },
        }

        # ── Call Gemini ────────────────────────────────────────────────────────
        if settings.GEMINI_API_KEY:
            primary = settings.GEMINI_MODEL.replace("models/", "")
            models_to_try = list(dict.fromkeys([
                primary, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"
            ]))

            for model_name in models_to_try:
                try:
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                    )
                    async with httpx.AsyncClient(timeout=20.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            return text.strip(), cited_ids
                except Exception:
                    continue

        # ── Fallback (no API key / all models failed) ──────────────────────────
        name = persona_json.get("identity", {}).get("name", "Mitra")
        concern = persona_json.get("lifeContext", {}).get("primaryConcern", "your concerns")
        best = passages[0] if passages else None

        fallback = (
            f"Namaste {name}. Jo aapne share kiya hai, woh sunkar mann bhaari ho gaya. "
            f"Aapki {concern} ke baare mein Gita kehti hai — "
        )
        if best:
            fallback += f'"{best.translation}" ({best.reference}). '
        fallback += "Kripya ek gehri saans lein. Main aapke saath hoon."

        return fallback, cited_ids
