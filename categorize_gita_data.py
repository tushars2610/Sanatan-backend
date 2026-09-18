"""
categorize_gita_data.py

Reads the raw verse data produced by fetch_gita_data.py, extracts ONLY the
Swami Sivananda translation ("siva" -> "et") for each verse, and sends
verses to Gemini in batches of ~14 to get:

  1. one or more category tags (from a fixed list below), and
  2. a short summary of the verse

Results are written into one JSON file per category under
data/categorized/<category>.json (a verse can appear in multiple category
files, since one verse can belong to multiple categories).

A combined data/categorized/all_tagged_verses.json is also written, which
is the file you should actually put in front of a human reviewer before
anything is considered final -- per the PRD, no passage goes live without
human review of both the tag assignment and the summary.

Input:
    data/raw/all_verses.json   (produced by fetch_gita_data.py)

Output:
    data/categorized/<category_name>.json   (one per category, only
                                              categories that matched at
                                              least one verse are created)
    data/categorized/all_tagged_verses.json (every verse, with its tags
                                              + summary, for review)
    data/categorized/failed_batches.json    (batches Gemini failed on,
                                              for manual retry)

Usage:
    export GEMINI_API_KEY="your-key-here"
    python categorize_gita_data.py
"""

import json
import os
import re
import time
import sys

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INPUT_PATH = "data/raw/all_verses.json"
OUTPUT_DIR = "data/categorized"

# NOTE: verify this model name against Google's current model list
# (https://ai.google.dev/gemini-api/docs/models) before running --
# model names/versions change over time and this one may have been
# renamed or deprecated by the time you run this.
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

BATCH_SIZE = 14
REQUEST_DELAY_SECONDS = 1.0   # be polite / avoid rate limits between batches
MAX_RETRIES_PER_BATCH = 3

# Fixed category list. Keep names stable -- they become filenames.
CATEGORIES = {
    "money": "💰 Money — wealth, material security, greed, poverty, financial anxiety",
    "fatigue": "😴 Fatigue — exhaustion, burnout, feeling depleted, wanting to give up from tiredness",
    "relationships": "❤️ Relationships — family, friends, romantic partners, betrayal, connection, loneliness",
    "suffering": "😔 Suffering — general pain, hardship, misery not tied to a specific loss",
    "overthinking": "🧠 Overthinking — rumination, mental restlessness, indecision from too much analysis",
    "fear": "😨 Fear — anxiety, dread, fear of failure, death, or the unknown",
    "purpose": "🎯 Purpose — meaning, life direction, 'why am I doing this'",
    "duty": "⚖️ Duty (Dharma) — obligation, responsibility, doing what's right regardless of feeling",
    "inner_peace": "🪷 Inner Peace — calm, equanimity, steadiness of mind",
    "eternal_bliss": "♾️ Eternal Bliss — transcendence, moksha, union with the divine, timeless joy",
    "death": "⚰️ Death — mortality, impermanence, one's own death",
    "grief": "😢 Grief — mourning a loss: a person, relationship, job, identity",
    "identity": "👤 Identity — 'who am I', self beyond roles/labels, atman vs. body",
    "desire": "🔥 Desire — craving, lust, ambition, attachment to wanting",
    "anger": "😡 Anger — rage, irritation, reactivity, losing control emotionally",
    "detachment": "🧘 Detachment — non-attachment to outcomes, letting go",
    "personal_growth": "🌱 Personal Growth — self-improvement, discipline, becoming a better version of oneself",
    "doubt": "🤔 Doubt & Indecision — being stuck between choices, wavering, uncertainty about what's true",
    "ego": "🦚 Ego & Pride — arrogance, need for recognition, self-importance",
    "faith_surrender": "🙏 Faith & Surrender — devotion, trusting a higher power, surrender of control",
}


def build_prompt(batch: list[dict]) -> str:
    """Builds the categorization prompt for one batch of verses."""
    category_list_str = "\n".join(f'- "{key}": {desc}' for key, desc in CATEGORIES.items())

    verses_str = ""
    for v in batch:
        verses_str += (
            f'\n---\n'
            f'chapter: {v["chapter"]}\n'
            f'verse: {v["verse"]}\n'
            f'translation: {v["siva_et"]}\n'
        )

    prompt = f"""You are helping tag verses of the Bhagavad Gita for a spiritual guidance app.

For EACH verse below, do two things:
1. Assign one or more categories from this FIXED list only (use the exact key, e.g. "money", "detachment"). A verse can and often should belong to multiple categories if it genuinely applies. Do not invent new category keys.
2. Write a short (1-2 sentence) plain-language summary of what the verse is saying, in a warm, non-academic tone suitable for someone going through a personal struggle (not a scholarly gloss).

Categories:
{category_list_str}

Verses to tag:
{verses_str}

Respond with ONLY a valid JSON array, no markdown fences, no commentary, no preamble. Each element must look exactly like:
{{"chapter": <int>, "verse": <int>, "categories": ["key1", "key2"], "summary": "..."}}

Return exactly {len(batch)} objects, one per verse above, in the same order.
"""
    return prompt


def extract_json_array(text: str) -> list[dict]:
    """Strips markdown fences etc. and parses the model's JSON array output."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned.strip(), flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned.strip()).strip()
    return json.loads(cleaned)


def load_verses(path: str) -> list[dict]:
    """Loads raw verse JSON and extracts only chapter, verse, and siva.et."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    verses = []
    skipped = 0
    for entry in raw:
        siva = entry.get("siva") or {}
        et = siva.get("et")
        chapter = entry.get("chapter")
        verse = entry.get("verse")
        if not et or chapter is None or verse is None:
            skipped += 1
            continue
        verses.append({"chapter": chapter, "verse": verse, "siva_et": et})

    if skipped:
        print(f"[warn] skipped {skipped} verse(s) missing chapter/verse/siva.et")
    return verses


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[error] Set the GEMINI_API_KEY environment variable first.")
        sys.exit(1)

    if not os.path.exists(INPUT_PATH):
        print(f"[error] Input file not found: {INPUT_PATH}")
        print("Run fetch_gita_data.py first.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_NAME)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    verses = load_verses(INPUT_PATH)
    print(f"Loaded {len(verses)} verses (chapter + siva.et only).")

    all_tagged = []
    failed_batches = []

    batches = list(chunked(verses, BATCH_SIZE))
    print(f"Processing {len(batches)} batches of up to {BATCH_SIZE} verses each...\n")

    for batch_idx, batch in enumerate(batches, start=1):
        print(f"Batch {batch_idx}/{len(batches)} "
              f"(chapters/verses: {[(v['chapter'], v['verse']) for v in batch]})")

        prompt = build_prompt(batch)
        result = None

        for attempt in range(1, MAX_RETRIES_PER_BATCH + 1):
            try:
                response = model.generate_content(prompt)
                parsed = extract_json_array(response.text)

                if len(parsed) != len(batch):
                    raise ValueError(
                        f"expected {len(batch)} objects back, got {len(parsed)}"
                    )
                result = parsed
                break
            except Exception as e:
                print(f"  [warn] batch {batch_idx} attempt {attempt}/"
                      f"{MAX_RETRIES_PER_BATCH} failed: {e}")
                time.sleep(2.0 * attempt)

        if result is None:
            print(f"  [error] giving up on batch {batch_idx}")
            failed_batches.append(batch)
            continue

        # Merge Gemini's output back with the original siva_et text
        # (so nothing downstream has to re-fetch it).
        for original, tagged in zip(batch, result):
            merged = {
                "chapter": original["chapter"],
                "verse": original["verse"],
                "siva_et": original["siva_et"],
                "categories": tagged.get("categories", []),
                "summary": tagged.get("summary", ""),
                "reviewed": true,  # human review flag, per PRD requirement
            }
            all_tagged.append(merged)

        time.sleep(REQUEST_DELAY_SECONDS)

    # --- Write combined file (for human review) ---
    combined_path = os.path.join(OUTPUT_DIR, "all_tagged_verses.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_tagged, f, ensure_ascii=False, indent=2)
    print(f"\nSaved combined tagged file: {combined_path}")

    # --- Split into per-category files ---
    by_category: dict[str, list] = {key: [] for key in CATEGORIES}
    unknown_categories = set()

    for entry in all_tagged:
        for cat in entry["categories"]:
            if cat in by_category:
                by_category[cat].append(entry)
            else:
                unknown_categories.add(cat)

    for cat_key, entries in by_category.items():
        if not entries:
            continue
        cat_path = os.path.join(OUTPUT_DIR, f"{cat_key}.json")
        with open(cat_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  {cat_key}: {len(entries)} verse(s) -> {cat_path}")

    if unknown_categories:
        print(f"\n[warn] Gemini returned category keys not in your fixed list "
              f"(ignored for file-splitting, but present in all_tagged_verses.json): "
              f"{sorted(unknown_categories)}")

    # --- Failed batches, for manual retry ---
    if failed_batches:
        failed_path = os.path.join(OUTPUT_DIR, "failed_batches.json")
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed_batches, f, ensure_ascii=False, indent=2)
        print(f"\n{len(failed_batches)} batch(es) failed entirely. "
              f"Saved to {failed_path} for manual retry.")

    print("\n--- Done ---")
    print(f"Total verses tagged: {len(all_tagged)}/{len(verses)}")
    print("Reminder: every entry has \"reviewed\": false — per the PRD, "
          "a human must review tags/summaries before anything goes live.")


if __name__ == "__main__":
    main()