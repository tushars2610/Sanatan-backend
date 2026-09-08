from datetime import date
from fastapi import APIRouter
from app.astronomy.engine import VedicAstronomyEngine

router = APIRouter(prefix="/content", tags=["Spiritual Content"])

QUOTES = [
    {
        "text": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन।",
        "translation": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action.",
        "source": "Bhagavad Gita 2.47",
    },
    {
        "text": "योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय।",
        "translation": "Be steadfast in yoga, perform your duty without attachment to success or failure.",
        "source": "Bhagavad Gita 2.48",
    },
    {
        "text": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत्।",
        "translation": "Elevate yourself through the power of your mind, and do not degrade yourself.",
        "source": "Bhagavad Gita 6.5",
    },
]


@router.get("/quote")
async def get_daily_quote():
    """Returns today's inspirational spiritual verse."""
    idx = date.today().toordinal() % len(QUOTES)
    return {"success": True, "quote": QUOTES[idx]}


@router.get("/today")
async def get_today_content(latitude: float = 28.6139, longitude: float = 77.2090):
    """Retrieve today's holistic spiritual summary: Panchang, quote, and reflection prompt."""
    today = date.today()
    panchang = VedicAstronomyEngine.calculate_panchang(target_date=today, latitude=latitude, longitude=longitude)
    quote = QUOTES[today.toordinal() % len(QUOTES)]

    return {
        "success": True,
        "date": today.isoformat(),
        "dailyQuote": quote,
        "panchangSummary": {
            "tithi": f"{panchang['tithi']['name']} ({panchang['tithi']['paksha'].capitalize()})",
            "nakshatra": panchang["nakshatra"]["name"],
            "vara": panchang["vara"]["nameEn"],
            "moonRashi": panchang["rashi"]["moon"]["nameEn"],
            "sunrise": panchang["sunrise"],
            "sunset": panchang["sunset"],
        },
        "reflectionPrompt": "Aaj apne karm par vishwas rakhein, parinaam ki chinta chhod kar sthir rahein.",
    }
