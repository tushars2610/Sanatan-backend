from typing import Dict, Any, List
import json
import httpx
from app.core.config import get_settings

settings = get_settings()


class ChatService:
    @staticmethod
    def _build_system_prompt(persona_json: Dict[str, Any]) -> str:
        name = persona_json.get("identity", {}).get("name", "Friend")
        lang = persona_json.get("identity", {}).get("preferredLanguage", "hi")
        deities = persona_json.get("spiritualConnection", {}).get("deities", [])
        concern = persona_json.get("lifeContext", {}).get("primaryConcern", "life and work")
        vedic = persona_json.get("vedicProfile", {})

        prompt = (
            "You are Sakha, a wise, compassionate, and non-judgmental spiritual companion.\n"
            f"The user's name is {name}.\n"
            f"The user's primary life concern is: {concern}.\n"
            f"The user feels connected with: {', '.join(deities) if deities else 'the divine'}.\n"
        )
        if vedic and "rashi" in vedic and "moon" in vedic["rashi"]:
            rashi_name = vedic["rashi"]["moon"].get("nameEn", "")
            nak_name = vedic.get("nakshatra", {}).get("name", "")
            prompt += f"Vedic astrological context: Moon Sign is {rashi_name}, Nakshatra is {nak_name}. "
            prompt += "Use this subtly when relevant, but DO NOT force astrology into every sentence.\n"

        prompt += (
            "\nSTRICT SAFETY & SYSTEM RULES:\n"
            "1. Be warm, patient, concise, and reflective.\n"
            "2. Never claim to be a deity, guru, or divine entity.\n"
            "3. Never provide medical, financial, or legal advice.\n"
            "4. Never make definitive or fear-inducing future predictions.\n"
            "5. Encourage positive inner reflection and practical mindfulness.\n"
            f"6. Respond primarily in {lang} or Hinglish/English according to user's tone.\n"
        )
        return prompt

    @classmethod
    async def generate_response(
        cls,
        user_message: str,
        persona_json: Dict[str, Any],
        recent_messages: List[Dict[str, str]],
    ) -> str:
        # If Gemini API key is configured, call Gemini API
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your-gemini-api-key-here":
            # Candidate models in priority order
            primary_model = settings.GEMINI_MODEL.replace("models/", "")
            candidate_models = [primary_model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
            # Deduplicate while preserving order
            models_to_try = list(dict.fromkeys(candidate_models))

            system_prompt = cls._build_system_prompt(persona_json)
            contents = []
            for msg in recent_messages[-6:]:
                contents.append({
                    "role": "user" if msg["role"] == "user" else "model",
                    "parts": [{"text": msg["content"]}]
                })
            contents.append({"role": "user", "parts": [{"text": user_message}]})

            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
            }

            for model_name in models_to_try:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(url, json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            text = data["candidates"][0]["content"]["parts"][0]["text"]
                            return text.strip()
                except Exception:
                    continue

        # Deterministic fallback companion response (always works even without external API key)
        name = persona_json.get("identity", {}).get("name", "Mitra")
        concern = persona_json.get("lifeContext", {}).get("primaryConcern", "chinta")
        deity = (persona_json.get("spiritualConnection", {}).get("deities") or ["Ishwar"])[0].title()

        return (
            f"Namaste {name}. Jo aapne saajha kiya hai, main samajh raha hoon. "
            f"Jab hum {concern} ke baare mein sochte hain, toh mann ka asantulit hona swabhavik hai. "
            f"Kripya ek gehri saans lein aur {deity} ka smaran karte hue apne mann ko shant karein. "
            "Ek samay par sirf vartamaan kadam par dhyan kendrit karein. Main sadaiv aapke saath hoon."
        )
