"""Stage B: Fetch sculptor metadata from Wikidata SPARQL.

Reads seeds.json.
- Seeds with known_qid: runs a batch properties query.
- Seeds without known_qid: runs a label search and prints candidates for
  manual confirmation (adds confirmed QID back to seeds.json manually).

Writes output/wikidata_raw.json — array of partial artist dicts ready for
editorial enrichment and merge.

Usage:
    python wikidata_fetch.py
    python wikidata_fetch.py --search-only   # only run label searches, skip known QIDs
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
except ImportError:
    sys.exit("Missing dependency: pip install SPARQLWrapper")

from schema import make_artist, slugify

SEEDS_PATH = Path(__file__).parent / "seeds.json"
OUTPUT_PATH = Path(__file__).parent / "output" / "wikidata_raw.json"
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
                print(f"  Rate-limited (429). Waiting {wait}s before retry {attempt+1}/{retries}...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError(f"SPARQL query failed after {retries} retries")


def val(binding: dict, key: str) -> str | None:
    return binding[key]["value"] if key in binding else None


def fetch_properties(qids: list[str]) -> list[dict]:
    """Batch-fetch sculptor properties for a list of QIDs."""
    values = " ".join(f"wd:{q}" for q in qids)
    # SERVICE wikibase:label auto-binds ?thingLabel for any bound ?thing variable
    # when the query uses the "en" language param. Do NOT add extra rdfs:label
    # or wdt: triples inside the SERVICE block — that causes Wikidata to return
    # labels for unrelated items.
    query = f"""
    SELECT DISTINCT ?person ?ulan ?viaf ?birth ?nationality ?city
                    ?wpTitle ?personLabel ?nationalityLabel ?cityLabel
    WHERE {{
      VALUES ?person {{ {values} }}
      OPTIONAL {{ ?person wdt:P245 ?ulan. }}
      OPTIONAL {{ ?person wdt:P214 ?viaf. }}
      OPTIONAL {{ ?person wdt:P569 ?birth. }}
      OPTIONAL {{ ?person wdt:P27 ?nationality. }}
      OPTIONAL {{ ?person wdt:P551 ?city. }}
      OPTIONAL {{
        ?wp schema:about ?person ;
            schema:isPartOf <https://en.wikipedia.org/> ;
            schema:name ?wpTitle.
      }}
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """
    rows = sparql_query(query)
    seen = {}
    for row in rows:
        qid = val(row, "person").split("/")[-1]
        if qid not in seen:
            seen[qid] = {
                "wikidata_qid": qid,
                "name": val(row, "personLabel"),
                "ulan_id": val(row, "ulan"),
                "viaf_id": val(row, "viaf"),
                "birth_year": _parse_year(val(row, "birth")),
                "nationality": val(row, "nationalityLabel"),
                "city": val(row, "cityLabel"),
                "wp_title": val(row, "wpTitle"),
            }
        else:
            # Merge multi-value fields (multiple nationalities, cities)
            rec = seen[qid]
            if not rec["nationality"] and val(row, "nationalityLabel"):
                rec["nationality"] = val(row, "nationalityLabel")
            if not rec["city"] and val(row, "cityLabel"):
                rec["city"] = val(row, "cityLabel")
    return list(seen.values())


def search_by_label(name: str) -> list[dict]:
    """Return top candidate QIDs for a sculptor name (for manual confirmation)."""
    query = f"""
    SELECT ?person ?personLabel ?birth ?nationalityLabel
    WHERE {{
      ?person wdt:P106 wd:Q1281618.     # occupation: sculptor
      ?person rdfs:label "{name}"@en.
      OPTIONAL {{ ?person wdt:P569 ?birth. }}
      OPTIONAL {{ ?person wdt:P27 ?nationality. }}
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
        ?nationality rdfs:label ?nationalityLabel.
        ?person rdfs:label ?personLabel.
      }}
    }}
    LIMIT 5
    """
    rows = sparql_query(query)
    candidates = []
    for row in rows:
        qid = val(row, "person").split("/")[-1]
        candidates.append({
            "qid": qid,
            "name": val(row, "personLabel"),
            "birth_year": _parse_year(val(row, "birth")),
            "nationality": val(row, "nationalityLabel"),
            "url": f"https://www.wikidata.org/wiki/{qid}",
        })
    return candidates


def search_by_label_broad(name: str) -> list[dict]:
    """Broader search — checks artists (not just sculptors) to handle mislabeled records."""
    query = f"""
    SELECT ?person ?personLabel ?birth ?nationalityLabel
    WHERE {{
      ?person wdt:P106/wdt:P279* wd:Q483501.  # artist or subclass
      ?person rdfs:label "{name}"@en.
      OPTIONAL {{ ?person wdt:P569 ?birth. }}
      OPTIONAL {{ ?person wdt:P27 ?nationality. }}
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
        ?nationality rdfs:label ?nationalityLabel.
        ?person rdfs:label ?personLabel.
      }}
    }}
    LIMIT 5
    """
    rows = sparql_query(query)
    candidates = []
    for row in rows:
        qid = val(row, "person").split("/")[-1]
        candidates.append({
            "qid": qid,
            "name": val(row, "personLabel"),
            "birth_year": _parse_year(val(row, "birth")),
            "nationality": val(row, "nationalityLabel"),
            "url": f"https://www.wikidata.org/wiki/{qid}",
        })
    return candidates


def _parse_year(iso_date: str | None) -> int | None:
    if not iso_date:
        return None
    try:
        return int(iso_date[:4])
    except (ValueError, IndexError):
        return None


def build_artist_record(seed: dict, props: dict | None) -> dict:
    """Merge a seed entry with Wikidata properties into a make_artist() dict."""
    name = seed["name"]
    living = seed.get("living", True)  # default True; seeds can override with false
    if props:
        artist = make_artist(
            name=props.get("name") or name,
            nationality=props.get("nationality") or "",
            city=props.get("city") or "",
            birth_year=props.get("birth_year"),
            wikidata_qid=props.get("wikidata_qid") or seed.get("known_qid"),
            ulan_id=props.get("ulan_id"),
            viaf_id=props.get("viaf_id"),
            instagram=seed.get("instagram"),
            living=living,
        )
        artist["_wp_title"] = props.get("wp_title")  # scratch field for bio enrichment
    else:
        artist = make_artist(
            name=name,
            wikidata_qid=seed.get("known_qid"),
            instagram=seed.get("instagram"),
            living=living,
        )
        artist["_wp_title"] = None
    artist["_notes"] = seed.get("notes", "")
    artist["_authority_status"] = "found" if props else "not_found"
    return artist


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--search-only", action="store_true",
                        help="Only run label searches for seeds without known_qid")
    args = parser.parse_args()

    seeds = json.loads(SEEDS_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(seeds)} seeds")

    results: list[dict] = []

    # --- Seeds with known QIDs: batch properties fetch ---
    known = [s for s in seeds if s.get("known_qid")]
    if known and not args.search_only:
        print(f"\nFetching Wikidata properties for {len(known)} known QIDs...")
        qids = [s["known_qid"] for s in known]
        # Wikidata SPARQL has ~100-item VALUES limit; chunk to be safe
        props_map: dict[str, dict] = {}
        for i in range(0, len(qids), 50):
            chunk = qids[i:i+50]
            print(f"  Querying batch {i//50 + 1}: {chunk}")
            props_list = fetch_properties(chunk)
            for p in props_list:
                props_map[p["wikidata_qid"]] = p
            time.sleep(1)  # polite pause

        for seed in known:
            qid = seed["known_qid"]
            props = props_map.get(qid)
            if not props:
                print(f"  WARNING: No Wikidata result for {seed['name']} ({qid})")
            record = build_artist_record(seed, props)
            results.append(record)

        # Save partial output so a crash during label search doesn't lose these
        OUTPUT_PATH.parent.mkdir(exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved {len(results)} records to {OUTPUT_PATH.name} (partial)")

    # --- Seeds without QIDs: label search ---
    unknown = [s for s in seeds if not s.get("known_qid")]
    if unknown:
        print(f"\nSearching Wikidata for {len(unknown)} seeds without QIDs...")
        for seed in unknown:
            name = seed["name"]
            print(f"\n  Searching: {name}")
            candidates = search_by_label(name)
            if not candidates:
                candidates = search_by_label_broad(name)
            if candidates:
                print(f"  Candidates (confirm manually, add known_qid to seeds.json):")
                for c in candidates:
                    print(f"    {c['qid']}  {c['name']}  b.{c['birth_year']}  "
                          f"{c['nationality']}  {c['url']}")
            else:
                print(f"  No Wikidata item found for '{name}' — will import with nulls")
            # Still emit a record with nulls so merge.py can process it
            record = build_artist_record(seed, None)
            results.append(record)
            time.sleep(0.5)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nWrote {len(results)} records to {OUTPUT_PATH}")
    found = sum(1 for r in results if r.get("_authority_status") == "found")
    print(f"Authority IDs resolved: {found}/{len(results)}")


if __name__ == "__main__":
    main()
