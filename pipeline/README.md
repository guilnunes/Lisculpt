# Lisculpt Import Pipeline

A repeatable four-stage Python pipeline for importing living sculptors and their
artworks from open institutional databases into `Lisculpt/sculptors.json`.

## Permissions summary

| Data | Source | License | Action needed |
|---|---|---|---|
| Biographical facts | Wikidata | CC0 | None |
| Artwork metadata | Wikidata, MoMA CSV | CC0 | None |
| Bio text (verbatim) | Wikipedia | CC-BY-SA | Attribute or rewrite |
| Artist authority records | Getty ULAN | ODC-BY | None (free to query) |
| Artwork images (living artists) | Any museum | Artist copyright | **Request per artist** |
| CC-licensed images | Wikimedia Commons | CC-BY / CC-BY-SA | Credit required |

## Setup

```bash
pip install SPARQLWrapper requests pandas rapidfuzz
```

Python 3.10+ required (uses `X | None` union syntax).

## Workflow

Run these stages in order for each batch:

### 1. Edit `seeds.json`

Add sculptor entries. For each artist, set `known_qid` if you have already
confirmed their Wikidata QID (look up at wikidata.org/wiki/Special:Search).

```json
{"name": "Kiki Smith", "known_qid": "Q234280", "instagram": "kikismith_artist", "notes": "American, b.1954"}
```

### 2. Fetch Wikidata properties

```bash
python wikidata_fetch.py
```

- Seeds with `known_qid`: batch SPARQL query for ULAN ID, VIAF ID, birth year,
  nationality, city, Wikipedia title.
- Seeds without `known_qid`: prints candidate QIDs for manual confirmation.
  Add confirmed QIDs back to `seeds.json`, then re-run.

Output: `output/wikidata_raw.json`

### 3. Fetch MoMA artworks

```bash
python moma_fetch.py
```

Downloads MoMA `Artworks.csv` and `Artists.csv` once to `cache/` (≈80 MB total).
Fuzzy-matches artist names and appends artwork arrays to matched records.
All artwork `image` fields are set to `null` — MoMA CC0 covers metadata only.

Output: updates `output/wikidata_raw.json` in place.

### 4. Enrich ULAN IDs

```bash
python ulan_fetch.py
```

For any record still missing `ulan_id`, queries Getty ULAN by name and
cross-checks birth year to avoid false positives.

Output: updates `output/wikidata_raw.json` in place.

### 5. Editorial pass

Copy `output/wikidata_raw.json` to `output/enriched.json` and edit manually:

- Write original `bio` text (or attribute Wikipedia CC-BY-SA source in `bio`).
- Set `country` (current practice country, not necessarily birth country).
- Assign `tags`, `themes`, `materials`, `rating`, `mould` flags.
- Set `featured: false` for all new imports initially.
- Confirm `living: true` — check `wikidata.org/wiki/{QID}` has no death date (P570).
- Verify Wikidata QID is the correct person (open the URL, read the description).
- Leave `avatar: null` and all artwork `image: null`.

### 6. Dry-run merge

```bash
python merge.py
```

Validates records, reports what would be added, what already exists, and any
enrichable fields for existing records (e.g. a `ulan_id` you can add manually).
No files are changed.

### 7. Write merge

```bash
python merge.py --write
```

Appends new artists to `Lisculpt/sculptors.json`. Additive only — never
overwrites existing records.

### 8. Verify

1. Open `Lisculpt/index.html` in a browser. New artists appear with placeholder tiles.
2. Click an artist card — verify the detail view renders.
3. Check Schema.org JSON-LD with [Google Rich Results Test](https://search.google.com/test/rich-results).
4. Commit only `Lisculpt/sculptors.json`. The `pipeline/` folder is a dev tool.

## Image upgrade path

After import, images can be added in three ways (in order of effort):

1. **Wikimedia Commons** — search for the sculptor; if a CC-licensed file exists,
   copy its URL to `artwork.image` and set `artwork.license` to the SPDX ID
   (e.g. `"CC-BY-SA-4.0"`).

2. **Artist DM** — send an Instagram DM asking for permission to use a specific
   image. Log consent in `seeds.json` under `"image_consent"`. Then download
   the image, commit it to `Lisculpt/images/{artist-slug}/01.jpg`, and update
   `artwork.image`.

3. **Never** use museum API image URLs for living artist works — the museum's CC0
   claim covers metadata only, not the artist's copyright in the work itself.

## Re-running for future batches

Edit `seeds.json` → run stages 2–7. `merge.py` is idempotent: it will skip any
artist already in `sculptors.json` and report enrichable field diffs for manual
review.
