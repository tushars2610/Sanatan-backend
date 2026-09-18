"""
fetch_gita_data.py

Fetches all Bhagavad Gita verses (chapter + verse) from the free,
open-source vedicscriptures API and saves them as JSON files.

API docs: https://github.com/vedicscriptures/bhagavad-gita-api
Base URL: https://vedicscriptures.github.io

Usage:
    python fetch_gita_data.py

Output:
    data/raw/chapter_<n>.json   -> one file per chapter (all its verses)
    data/raw/all_verses.json    -> single combined file, all 700 verses

Each verse's raw JSON looks roughly like:
{
    "chapter": 2,
    "verse": 47,
    "slok": "<Sanskrit devanagari text>",
    "transliteration": "<Roman transliteration>",
    "word_meanings": "<word-by-word meaning string>",
    "siva": {"author": "Swami Sivananda", "et": "...", "ec": "..."},
    "purohit": {"author": "Shri Purohit Swami", "et": "..."},
    "chinmay": {"author": "Swami Chinmayananda", "hc": "..."},
    "prabhu": {"author": "A.C. Bhaktivedanta Swami Prabhupada", "et": "...", "ec": "..."},
    ... (other translators)
}

We don't reshape the data here — this script's only job is to pull the
raw source data down reliably and save it, so nothing gets lost.
Reshaping into your DB schema (summary / exact meaning / context / mantra)
happens in a separate transform step, after you review/pick translators
and licensing (see PRD open question on translation rights).
"""

import json
import os
import time
import sys
import requests

BASE_URL = "https://vedicscriptures.github.io"

# Verse counts per chapter (1-indexed), Bhagavad Gita has 18 chapters, 700 verses total.
CHAPTER_VERSE_COUNTS = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47,
    7: 30, 8: 28, 9: 34, 10: 42, 11: 55, 12: 20,
    13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78,
}

OUTPUT_DIR = "data/raw"
REQUEST_DELAY_SECONDS = 0.3  # be polite to the free API, avoid hammering it
MAX_RETRIES = 3


def fetch_verse(chapter: int, verse: int) -> dict | None:
    """Fetch a single verse's JSON from the API, with basic retry logic."""
    url = f"{BASE_URL}/slok/{chapter}/{verse}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"  [warn] {chapter}.{verse} -> HTTP {resp.status_code} "
                      f"(attempt {attempt}/{MAX_RETRIES})")
        except requests.RequestException as e:
            print(f"  [warn] {chapter}.{verse} -> {e} (attempt {attempt}/{MAX_RETRIES})")
        time.sleep(1.0 * attempt)  # backoff
    print(f"  [error] giving up on chapter {chapter}, verse {verse}")
    return None


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_verses = []
    failed = []

    total_verses = sum(CHAPTER_VERSE_COUNTS.values())
    fetched_count = 0

    for chapter, verse_count in CHAPTER_VERSE_COUNTS.items():
        print(f"Chapter {chapter}: fetching {verse_count} verses...")
        chapter_verses = []

        for verse in range(1, verse_count + 1):
            data = fetch_verse(chapter, verse)
            if data is not None:
                chapter_verses.append(data)
                all_verses.append(data)
                fetched_count += 1
            else:
                failed.append((chapter, verse))

            time.sleep(REQUEST_DELAY_SECONDS)

        # Save one file per chapter as we go, so partial progress isn't lost
        # if the script is interrupted partway through.
        chapter_path = os.path.join(OUTPUT_DIR, f"chapter_{chapter}.json")
        with open(chapter_path, "w", encoding="utf-8") as f:
            json.dump(chapter_verses, f, ensure_ascii=False, indent=2)

        print(f"  -> saved {len(chapter_verses)}/{verse_count} verses to {chapter_path}")

    # Save the combined file
    combined_path = os.path.join(OUTPUT_DIR, "all_verses.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(all_verses, f, ensure_ascii=False, indent=2)

    print("\n--- Done ---")
    print(f"Fetched {fetched_count}/{total_verses} verses successfully.")
    print(f"Combined file: {combined_path}")

    if failed:
        print(f"\n{len(failed)} verse(s) failed and need a retry:")
        for ch, vs in failed:
            print(f"  chapter {ch}, verse {vs}")
        failed_path = os.path.join(OUTPUT_DIR, "failed_verses.json")
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2)
        print(f"List saved to {failed_path} — rerun fetch_verse() on these manually if needed.")
        sys.exit(1)


if __name__ == "__main__":
    main()