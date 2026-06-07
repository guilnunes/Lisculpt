"""Stage C: Match seeds against the MoMA open-access collection CSV (CC0 metadata).

Downloads Artworks.csv and Artists.csv from the MoMA GitHub repo once and caches
them in pipeline/cache/. Fuzzy-matches sculptor names from output/wikidata_raw.json
and appends artwork arrays to matched records.

Writes output/wikidata_raw.json in place (adds/replaces the artworks[] key).

Usage:
    python moma_fetch.py
    python moma_fetch.py --no-download   # use cached CSVs, skip network fetch
    python moma_fetch.py --threshold 85  # fuzzy match score threshold (default 80)

Image note: MoMA's CC0 license covers metadata only.
Image URLs from this data must NOT be used — set image: null for all artworks.
"""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    sys.exit("Missing dependency: pip install pandas")

try:
    from rapidfuzz import fuzz, process as rfprocess
except ImportError:
    sys.exit("Missing dependency: pip install rapidfuzz")

from schema import make_artwork, slugify

CACHE_DIR = Path(__file__).parent / "cache"
OUTPUT_PATH = Path(__file__).parent / "output" / "wikidata_raw.json"

ARTWORKS_URL = (
    "https://media.githubusercontent.com/media/MuseumofModernArt/collection"
    "/main/Artworks.csv"
)
ARTISTS_URL = (
    "https://media.githubusercontent.com/media/MuseumofModernArt/collection"
    "/main/Artists.csv"
)
ARTWORKS_CACHE = CACHE_DIR / "moma_artworks.csv"
ARTISTS_CACHE = CACHE_DIR / "moma_artists.csv"

# Dimensions regex: captures "h × w × d" or "h × w" in cm or inches
DIM_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:×|x|X)\s*(\d+(?:[.,]\d+)?)"
    r"(?:\s*(?:×|x|X)\s*(\d+(?:[.,]\d+)?))?",
    re.IGNORECASE,
)
CM_RE = re.compile(r"\((\d+(?:[.,]\d+)?)\s*(?:×|x|X)\s*(\d+(?:[.,]\d+)?)"
                   r"(?:\s*(?:×|x|X)\s*(\d+(?:[.,]\d+)?))?\s*cm\)", re.IGNORECASE)


def download(url: str, dest: Path):
    print(f"  Downloading {dest.name} ...")
    urllib.request.urlretrieve(url, dest)
    print(f"  Done ({dest.stat().st_size // 1024} KB)")


def parse_year(raw: str) -> int | None:
    if not raw or not isinstance(raw, str):
        return None
    m = re.search(r"\b(1[89]\d\d|20\d\d)\b", raw)
    return int(m.group(1)) if m else None


def parse_dimensions_cm(raw: str) -> tuple[float | None, float | None, float | None]:
    """Return (height_cm, width_cm, depth_cm) from a MoMA Dimensions string."""
    if not raw or not isinstance(raw, str):
        return None, None, None
    # Prefer cm values in parentheses
    m = CM_RE.search(raw)
    if m:
        h = float(m.group(1).replace(",", "."))
        w = float(m.group(2).replace(",", "."))
        d = float(m.group(3).replace(",", ".")) if m.group(3) else None
        return h, w, d
    return None, None, None


def normalize_material(raw: str) -> str:
    """Return a clean material label from a MoMA Medium string."""
    if not raw or not isinstance(raw, str):
        return ""
    # Strip long descriptions, keep up to first semicolon or period
    short = re.split(r"[;.]", raw)[0].strip()
    # Collapse "Cast" prefixes
    short = re.sub(r"^Cast\s+", "", short, flags=re.IGNORECASE)
    return short[:80]  # cap length


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument("--threshold", type=int, default=80)
    args = parser.parse_args()

    CACHE_DIR.mkdir(exist_ok=True)

    if not args.no_download:
        if not ARTWORKS_CACHE.exists():
            download(ARTWORKS_URL, ARTWORKS_CACHE)
        else:
            print(f"Using cached {ARTWORKS_CACHE.name}")
        if not ARTISTS_CACHE.exists():
            download(ARTISTS_URL, ARTISTS_CACHE)
        else:
            print(f"Using cached {ARTISTS_CACHE.name}")
    else:
        if not ARTWORKS_CACHE.exists() or not ARTISTS_CACHE.exists():
            sys.exit("Cached CSVs not found. Run without --no-download first.")

    print("\nLoading MoMA CSVs...")
    artworks_df = pd.read_csv(ARTWORKS_CACHE, low_memory=False, dtype=str)
    print(f"  Artworks: {len(artworks_df):,} rows")

    # Filter to sculpture
    sculpture_mask = (
        artworks_df["Classification"].fillna("").str.contains(
            r"sculpture|Sculpture", case=False, regex=True
        )
    )
    sculptures = artworks_df[sculpture_mask].copy()
    print(f"  Sculpture works: {len(sculptures):,}")

    # Load intermediate results
    if not OUTPUT_PATH.exists():
        sys.exit(f"Run wikidata_fetch.py first — {OUTPUT_PATH} not found")
    records = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    print(f"\nMatching {len(records)} pipeline records against MoMA...")

    # Build lookup: artist display name → set of rows
    moma_artist_names = sculptures["Artist"].dropna().unique().tolist()

    matched_total = 0
    for record in records:
        name = record["name"]
        # Fuzzy match against MoMA artist column
        match = rfprocess.extractOne(
            name, moma_artist_names, scorer=fuzz.WRatio, score_cutoff=args.threshold
        )
        if not match:
            print(f"  No MoMA match: {name}")
            continue
        moma_name, score, _ = match
        print(f"  Matched: '{name}' -> '{moma_name}' (score {score})")

        artist_works = sculptures[sculptures["Artist"] == moma_name]
        # Take up to 4 works; prefer those with dimensions
        has_dims = artist_works[artist_works["Dimensions"].notna() &
                                (artist_works["Dimensions"] != "")]
        no_dims = artist_works[~artist_works.index.isin(has_dims.index)]
        selected = pd.concat([has_dims.head(3), no_dims.head(1)]).head(4)

        artist_id = slugify(name)
        artworks = []
        for i, (_, row) in enumerate(selected.iterrows(), start=1):
            raw_title = row.get("Title", "") or ""
            raw_mat = row.get("Medium", "") or ""
            raw_year = row.get("Date", "") or ""
            raw_dims = row.get("Dimensions", "") or ""

            h, w, d = parse_dimensions_cm(raw_dims)
            artwork = make_artwork(
                artist_id=artist_id,
                seq=i,
                title=raw_title.strip(),
                year=parse_year(raw_year),
                material=normalize_material(raw_mat),
                height_cm=h,
                width_cm=w,
                depth_cm=d,
                location_country="United States",  # MoMA collection, New York
                license=None,  # image not used; metadata is CC0
            )
            artworks.append(artwork)

        record["artworks"] = artworks
        matched_total += 1

    OUTPUT_PATH.write_text(
        json.dumps(records, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\nUpdated {OUTPUT_PATH.name}: {matched_total}/{len(records)} artists matched in MoMA")


if __name__ == "__main__":
    main()
