"""Stage: Getty ULAN authority enrichment.

For any record in output/wikidata_raw.json that still has ulan_id: null,
queries the Getty ULAN SPARQL endpoint by artist name.
Cross-checks birth year to avoid false positives.

Updates output/wikidata_raw.json in place.

Usage:
    python ulan_fetch.py
    python ulan_fetch.py --force   # re-query even records that already have ulan_id
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

OUTPUT_PATH = Path(__file__).parent / "output" / "wikidata_raw.json"
GETTY_ENDPOINT = "https://vocab.getty.edu/sparql.json"
USER_AGENT = "Lisculpt-pipeline/1.0 (https://github.com/guilnunes/Lisculpt)"


def getty_sparql(query: str) -> list[dict]:
    sparql = SPARQLWrapper(GETTY_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
    sparql.setQuery(query)
    sparql.setReturnFormat(SPARQL_JSON)
    results = sparql.query().convert()
    return results["results"]["bindings"]


def val(binding: dict, key: str) -> str | None:
    return binding[key]["value"] if key in binding else None


def search_ulan(name: str, birth_year: int | None = None) -> str | None:
    """Return a ULAN numeric ID for the given artist name, or None."""
    # ULAN full-text search via luc:term
    query = f"""
    SELECT ?subject ?prefLabel ?birthYear WHERE {{
      ?subject a gvp:PersonConcept ;
               gvp:prefLabelGVP/xl:literalForm ?prefLabel .
      ?prefLabel bif:contains '"{name}"' .
      OPTIONAL {{
        ?subject gvp:estStart ?birthYear .
      }}
    }}
    LIMIT 10
    """
    try:
        rows = getty_sparql(query)
    except Exception as e:
        print(f"    Getty SPARQL error for '{name}': {e}")
        return None

    if not rows:
        return None

    for row in rows:
        label = val(row, "prefLabel") or ""
        subj = val(row, "subject") or ""
        raw_birth = val(row, "birthYear")
        ulan_birth = int(raw_birth[:4]) if raw_birth else None
        ulan_id = subj.split("/")[-1] if subj else None

        # Confirm by name similarity and birth year (if known)
        name_match = name.lower() in label.lower() or label.lower() in name.lower()
        year_ok = (
            birth_year is None
            or ulan_birth is None
            or abs(birth_year - ulan_birth) <= 2
        )
        if name_match and year_ok:
            return ulan_id

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Re-query even records that already have ulan_id")
    args = parser.parse_args()

    if not OUTPUT_PATH.exists():
        sys.exit(f"Run wikidata_fetch.py first — {OUTPUT_PATH} not found")

    records = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    need_ulan = [r for r in records if args.force or not r.get("ulan_id")]
    print(f"Records needing ULAN lookup: {len(need_ulan)}/{len(records)}")

    updated = 0
    for record in need_ulan:
        name = record["name"]
        birth_year = record.get("birth_year")
        print(f"  Querying ULAN for: {name} (b.{birth_year})")
        ulan_id = search_ulan(name, birth_year)
        if ulan_id:
            record["ulan_id"] = ulan_id
            print(f"    Found ULAN: {ulan_id}")
            updated += 1
        else:
            print(f"    Not found in ULAN")
            record.setdefault("_authority_status", "not_found")
        time.sleep(1)  # polite pause

    OUTPUT_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nUpdated {updated} ULAN IDs. Wrote {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
