import json
import logging

from src.config import get_groq_client, call_groq_with_retry

logger = logging.getLogger(__name__)


async def generate_tiktok_caption(topic: str, trending_queries: list[str], config: dict) -> dict:
    """Call Groq (free tier) to turn a topic + trend signal into a TikTok caption + hashtags."""
    client = get_groq_client(config)
    model = config.get("ai", {}).get("text_model", "openai/gpt-oss-120b")
    trending_str = ", ".join(trending_queries) if trending_queries else "(none found)"

    response_text = await call_groq_with_retry(
        client,
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a TikTok growth expert who writes short, scroll-stopping captions "
                    "optimized for the For You Page. Return ONLY valid JSON."
                ),
            },
            {
                "role": "user",
                "content": f"""Write a TikTok caption for a video about: "{topic}"

Currently trending/rising search queries around this topic (last 7 days): {trending_str}

Rules:
- caption: 1-2 short punchy lines, hook first (first 6 words matter most, before the "...more" cutoff). No long paragraphs. Emojis allowed but not excessive.
- hashtags: a list of 5-8 hashtags (no # symbol, code will add it): mix 1-2 broad massive-reach tags (e.g. category-level, fyp-style), then specific/trending niche tags. Prioritize wording from the trending queries when it fits.

Return JSON with exactly these keys: caption, hashtags""",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.8,
        max_tokens=1024,
        reasoning_effort="low",
    )

    data = json.loads(response_text)
    return {
        "caption": str(data["caption"])[:2200],
        "hashtags": [str(h) for h in data.get("hashtags", [])][:8],
    }
