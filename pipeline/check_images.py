"""Check availability of public images on Wikimedia Commons for imported artists.

Reads sculptors.json, finds artists with a wikidata_qid but no avatar image,
queries Wikidata P18 (portrait) and P800 (notable works) + their P18 images,
and prints a markdown-style report to stdout. Makes no changes to any file.

Usage:
    python check_images.py
"""

import json
import sys
import time
from pathlib import Path

try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
except ImportError:
    sys.exit("Missing dependency: pip install SPARQLWrapper")

SCULPTORS_PATH = Path(__file__).parent.parent / "Lisculpt" / "sculptors.json"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "Lisculpt-pipeline/1.0 (https://github.com/guilnunes/Lisculpt)"


def sparql_query(query: str, retries: int = 3) -> list[dict]:
    from urllib.error import HTTPError
    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(SPARQL_JSON)
    for attempt in range(retries):
        try:
            results = sparql.query().convert()
            return results["results"]["bindings"]
        except HTTPError as e:
            if e.code == 429:
                wait = 65 * (attempt + 1)
                print(f"Rate-limited (429). Waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"SPARQL query failed after {retries} retries")


def val(binding: dict, key: str) -> str | None:
    return binding[key]["value"] if key in binding else None


def fetch_images(qids: list[str]) -> dict:
    """Return {qid: {"portrait": url|None, "works": [(title, image_url)]}}"""
    values = " ".join(f"wd:{q}" for q in qids)
    query = f"""
    SELECT ?person ?portrait ?work ?workLabel ?workImage
    WHERE {{
      VALUES ?person {{ {values} }}
      OPTIONAL {{ ?person wdt:P18 ?portrait. }}
      OPTIONAL {{
        ?person wdt:P800 ?work.
        OPTIONAL {{ ?work wdt:P18 ?workImage. }}
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    rows = sparql_query(query)
    result: dict[str, dict] = {}
    for row in rows:
        qid = val(row, "person").split("/")[-1]
        if qid not in result:
            result[qid] = {"portrait": None, "works": []}
        rec = result[qid]
        if val(row, "portrait") and not rec["portrait"]:
            rec["portrait"] = val(row, "portrait")
        work_title = val(row, "workLabel")
        work_image = val(row, "workImage")
        if work_title and work_image:
            entry = (work_title, work_image)
            if entry not in rec["works"]:
                rec["works"].append(entry)
    return result


def main():
    data = json.loads(SCULPTORS_PATH.read_text(encoding="utf-8"))
    sculptors = data["artists"]
    targets = [a for a in sculptors if a.get("wikidata_qid") and not a.get("avatar")]
    if not targets:
        print("No artists with wikidata_qid and missing avatar found.")
        return

    print(f"Checking {len(targets)} artists with Wikidata QIDs but no avatar...\n")
    qids = [a["wikidata_qid"] for a in targets]

    print("Querying Wikidata (P18 portrait + P800 notable works)...", flush=True)
    images = fetch_images(qids)

    print("\n## Public image availability\n")
    header = f"{'Artist':<30} {'Portrait':<10} {'Artwork images'}"
    print(header)
    print("-" * 60)

    artists_with_portrait = []
    artists_with_artwork_images = []

    for a in targets:
        qid = a["wikidata_qid"]
        name = a["name"]
        data = images.get(qid, {"portrait": None, "works": []})
        portrait_url = data["portrait"]
        work_images = [(t, u) for t, u in data["works"] if u]

        has_portrait = "YES" if portrait_url else "no"
        work_label = str(len(work_images)) if work_images else "none"
        print(f"{name:<30} {has_portrait:<10} {work_label}")

        if portrait_url:
            artists_with_portrait.append((name, qid, portrait_url))
        if work_images:
            artists_with_artwork_images.append((name, qid, work_images))

    print(f"\n{'='*60}")
    print(f"\nPortrait images available:  {len(artists_with_portrait)}/{len(targets)} artists")
    print(f"Artwork images available:   {len(artists_with_artwork_images)}/{len(targets)} artists")

    if artists_with_portrait:
        print("\n### Portrait URLs\n")
        for name, qid, url in artists_with_portrait:
            print(f"{name} ({qid})")
            print(f"  {url}")

    if artists_with_artwork_images:
        print("\n### Artwork image URLs\n")
        for name, qid, works in artists_with_artwork_images:
            print(f"{name} ({qid})")
            for title, url in works:
                print(f"  - {title}")
                print(f"    {url}")


if __name__ == "__main__":
    main()
