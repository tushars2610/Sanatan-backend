import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from google import genai
from google.genai import types

from app.db.models.models import User, UserProfile, BirthProfile, AstrologySnapshot
from app.schemas.persona import (
    LLMGeneratedInsights,
    PersonaIdentity,
    PersonaLifeContext,
    PersonaSpiritualConnection,
    PersonaVedicProfile,
    CanonicalPersonaSchema,
    SakhaPersona,
)


class PersonaService:
    @staticmethod
    async def build_canonical_persona_async(
        user: User,
        profile: Optional[UserProfile] = None,
        birth: Optional[BirthProfile] = None,
        snapshot: Optional[AstrologySnapshot] = None,
    ) -> Dict[str, Any]:
        """Constructs the canonical SpiritualSakha Persona JSON asynchronously using Gemini."""
        has_birth = birth is not None and birth.date_of_birth is not None
        has_astro = snapshot is not None and bool(snapshot.rashi)
        completeness = 2 if has_astro else (1 if has_birth else 0)

        # Stage A: Deterministic profile builder
        life_stage_val = (profile.current_state if profile and profile.current_state else (profile.life_stage if profile else "professional"))
        primary_concern_val = (profile.seeking if profile and profile.seeking else (profile.primary_concern if profile else "peace and focus"))

        identity = PersonaIdentity(
            name=user.full_name or "Friend",
            preferred_language=user.preferred_language,
            timezone=user.timezone,
            life_stage=life_stage_val,
        )

        life_context = PersonaLifeContext(
            primary_concern=primary_concern_val,
            faith_level=profile.faith_level if profile else "occasional",
            tradition=profile.tradition if profile else "hindu",
        )

        deities_list = []
        if profile and profile.deity:
            deities_list = [profile.deity.lower()]
        elif profile and profile.deities:
            deities_list = profile.deities
        else:
            deities_list = ["shiva", "hanuman"]

        spiritual_connection = PersonaSpiritualConnection(
            deities=deities_list,
            current_practices=profile.current_practices if (profile and profile.current_practices is not None) else ["prayer", "reflection"],
            daily_time_minutes=profile.daily_time_minutes if (profile and profile.daily_time_minutes is not None) else 10,
        )

        vedic_profile = PersonaVedicProfile()
        if has_astro:
            vedic_profile.rashi_name = snapshot.rashi.get("nameEn") if snapshot.rashi else None
            vedic_profile.ruling_planet = snapshot.rashi.get("rulingPlanet") if snapshot.rashi else None
            vedic_profile.nakshatra_name = snapshot.nakshatra.get("name") if snapshot.nakshatra else None

        # Stage B: Persona LLM Generation using Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        
        ai_insights = None
        if not api_key:
            # Fallback if no API key is provided
            print("WARNING: GEMINI_API_KEY not found. Using fallback AI insights.")
            ai_insights = LLMGeneratedInsights(
                sakha_persona=SakhaPersona(
                    communication_style="warm and concise",
                    preferred_tone="calm",
                    guidance_style=["practical"],
                    topics_to_emphasize=["peace"]
                ),
                deity_practices=[],
                astrological_traits=None,
                recommended_daily_habits=["Morning meditation", "Gratitude journaling"]
            )
        else:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            You are a backend persona builder for a spiritual application named SpiritualSakha.
            Generate personalized spiritual insights for the user based on their deterministic profile:
            Identity: {identity.model_dump_json()}
            Life Context: {life_context.model_dump_json()}
            Spiritual Connection: {spiritual_connection.model_dump_json()}
            Vedic Astrology Profile: {vedic_profile.model_dump_json()}
            
            Return the output adhering strictly to the provided JSON schema.
            """
            
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=LLMGeneratedInsights,
                    ),
                )
                ai_insights_dict = json.loads(response.text)
                ai_insights = LLMGeneratedInsights(**ai_insights_dict)
            except Exception as e:
                print(f"Failed to parse Gemini response: {e}. Falling back.")
                ai_insights = LLMGeneratedInsights(
                    sakha_persona=SakhaPersona(
                        communication_style="warm and concise",
                        preferred_tone="calm",
                        guidance_style=["practical"],
                        topics_to_emphasize=["peace"]
                    ),
                    deity_practices=[],
                    astrological_traits=None,
                    recommended_daily_habits=["Morning meditation", "Gratitude journaling"]
                )

        canonical_persona = CanonicalPersonaSchema(
            generated_at=datetime.utcnow().isoformat() + "Z",
            identity=identity,
            life_context=life_context,
            spiritual_connection=spiritual_connection,
            vedic_profile=vedic_profile,
            ai_insights=ai_insights
        )

        canonical_dict = canonical_persona.model_dump()
        canonical_dict["completenessLevel"] = completeness  # needed by DB model logic in users.py
        
        return canonical_dict
