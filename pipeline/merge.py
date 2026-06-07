"""Stage D: Validate and merge enriched records into sculptors.json.

Reads output/enriched.json (the post-editorial version of wikidata_raw.json).
Performs validation, then additively merges new artists into sculptors.json.

Rules:
- Additive only: never overwrites an existing artist record.
- If a QID or slug already exists, logs a skip with any enrichable field diffs.
- Strips scratch fields (_wp_title, _notes, _authority_status) before writing.
- Preserves exact 2-space indent and field order of sculptors.json.

Usage:
    python merge.py                   # dry run (shows what would change)
    python merge.py --write           # actually update sculptors.json
    python merge.py --input custom.json --write
"""

import argparse
import json
import sys
from pathlib import Path

from schema import slugify, MATERIAL_AAT

ENRICHED_PATH = Path(__file__).parent / "output" / "enriched.json"
SCULPTORS_PATH = Path(__file__).parent.parent / "Lisculpt" / "sculptors.json"

SCRATCH_FIELDS = {"_wp_title", "_notes", "_authority_status"}

REQUIRED_ARTIST_FIELDS = {"id", "name", "living"}
VALID_AAT_URIS = set(MATERIAL_AAT.values())


# ── Validation ────────────────────────────────────────────────────────────────

class ValidationWarning:
    def __init__(self, name: str, field: str, msg: str):
        self.name = name
        self.field = field
        self.msg = msg

    def __str__(self):
        return f"[{self.name}] {self.field}: {self.msg}"


def validate_artist(artist: dict) -> list[ValidationWarning]:
    warnings: list[ValidationWarning] = []
    name = artist.get("name", "?")

    for f in REQUIRED_ARTIST_FIELDS:
        if artist.get(f) is None:
            warnings.append(ValidationWarning(name, f, "required field is null"))

    if artist.get("living") is None:
        warnings.append(ValidationWarning(name, "living", "field is null (should be true or false)"))

    # Slug consistency
    expected_slug = slugify(name)
    if artist.get("id") != expected_slug:
        warnings.append(ValidationWarning(name, "id",
                                          f"slug mismatch: stored={artist.get('id')!r} "
                                          f"expected={expected_slug!r}"))

    # AAT URI validity
    for artwork in artist.get("artworks", []):
        uri = artwork.get("material_aat_uri")
        if uri and uri not in VALID_AAT_URIS:
            warnings.append(ValidationWarning(
                name, f"artworks[{artwork.get('id')}].material_aat_uri",
                f"unknown AAT URI: {uri}"
            ))

    # Duplicate artwork IDs within artist
    artwork_ids = [a.get("id") for a in artist.get("artworks", [])]
    seen_ids: set = set()
    for aid in artwork_ids:
        if aid in seen_ids:
            warnings.append(ValidationWarning(name, "artworks", f"duplicate id: {aid}"))
        seen_ids.add(aid)

    return warnings


# ── Diff helper ───────────────────────────────────────────────────────────────

ENRICHABLE = {"ulan_id", "viaf_id", "wikidata_qid", "birth_year", "nationality",
              "city", "country", "instagram"}


def diff_enrichable(existing: dict, incoming: dict) -> dict:
    """Return fields that incoming has but existing lacks (null → value)."""
    diffs = {}
    for f in ENRICHABLE:
        ex_val = existing.get(f)
        in_val = incoming.get(f)
        if (ex_val is None or ex_val == "") and (in_val is not None and in_val != ""):
            diffs[f] = in_val
    return diffs


# ── Merge ─────────────────────────────────────────────────────────────────────

def clean_artist(artist: dict) -> dict:
    """Remove scratch fields before writing to sculptors.json."""
    return {k: v for k, v in artist.items() if k not in SCRATCH_FIELDS}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="Write changes to sculptors.json (default: dry run)")
    parser.add_argument("--input", default=str(ENRICHED_PATH),
                        help=f"Path to enriched JSON (default: {ENRICHED_PATH})")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Input file not found: {input_path}\n"
                 "Run wikidata_fetch.py → moma_fetch.py → ulan_fetch.py first,\n"
                 "then do the editorial pass and save as output/enriched.json")

    incoming: list[dict] = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"Incoming records: {len(incoming)}")

    if not SCULPTORS_PATH.exists():
        sys.exit(f"sculptors.json not found at {SCULPTORS_PATH}")

    data = json.loads(SCULPTORS_PATH.read_text(encoding="utf-8"))
    existing_artists: list[dict] = data["artists"]

    # Build lookup maps
    existing_by_slug = {a["id"]: a for a in existing_artists}
    existing_by_qid = {
        a["wikidata_qid"]: a for a in existing_artists if a.get("wikidata_qid")
    }

    # Validate incoming first
    all_warnings: list[ValidationWarning] = []
    for artist in incoming:
        all_warnings.extend(validate_artist(artist))

    if all_warnings:
        print(f"\n{len(all_warnings)} validation warning(s):")
        for w in all_warnings:
            print(f"  WARN  {w}")
    else:
        print("Validation: all records clean")

    # Check for duplicate QIDs within the incoming batch itself
    incoming_qids: dict[str, str] = {}
    for artist in incoming:
        qid = artist.get("wikidata_qid")
        if qid:
            if qid in incoming_qids:
                print(f"  ERROR duplicate QID {qid} in incoming: "
                      f"{incoming_qids[qid]} and {artist['name']}")
            else:
                incoming_qids[qid] = artist["name"]

    # Classify each incoming record
    to_add: list[dict] = []
    skipped: list[tuple[str, str]] = []  # (name, reason)
    enrichable: list[tuple[str, dict]] = []  # (name, diff)

    for artist in incoming:
        slug = artist.get("id") or slugify(artist["name"])
        qid = artist.get("wikidata_qid")

        existing = existing_by_slug.get(slug) or (existing_by_qid.get(qid) if qid else None)
        if existing:
            diffs = diff_enrichable(existing, artist)
            if diffs:
                enrichable.append((artist["name"], diffs))
            skipped.append((artist["name"],
                            f"already in sculptors.json (id={existing['id']})"))
            continue

        to_add.append(artist)

    # Report
    print(f"\n{'DRY RUN — ' if not args.write else ''}Summary:")
    print(f"  Add:  {len(to_add)}")
    print(f"  Skip (already exists): {len(skipped)}")

    if skipped:
        print("\nSkipped:")
        for name, reason in skipped:
            print(f"  {name}: {reason}")

    if enrichable:
        print(f"\nEnrichable fields on existing records (apply manually):")
        for name, diffs in enrichable:
            for field, value in diffs.items():
                print(f"  {name}.{field} = {value!r}")

    if not to_add:
        print("\nNothing to add.")
        return

    print(f"\nRecords to add:")
    for a in to_add:
        print(f"  {a['name']} ({a.get('wikidata_qid') or 'no QID'}) "
              f"— {len(a.get('artworks', []))} artworks")

    if not args.write:
        print("\nDry run complete. Pass --write to update sculptors.json.")
        return

    # Validate JSON round-trip before writing
    cleaned = [clean_artist(a) for a in to_add]
    data["artists"].extend(cleaned)
    output = json.dumps(data, indent=2, ensure_ascii=False)
    try:
        json.loads(output)
    except json.JSONDecodeError as e:
        sys.exit(f"JSON validation failed before write: {e}")

    SCULPTORS_PATH.write_text(output + "\n", encoding="utf-8")
    print(f"\nWrote {len(to_add)} new artist(s) to {SCULPTORS_PATH}")
    print("Total artists in sculptors.json:", len(data["artists"]))


if __name__ == "__main__":
    main()
