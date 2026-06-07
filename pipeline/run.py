"""Lisculpt artist-batch pipeline runner.

Stages:
  A  wikidata_fetch — Wikidata SPARQL: metadata for artists in seeds.json
  B  moma_fetch     — MoMA CC0 CSV: artworks matched by sculptor name
  C  ulan_fetch     — Getty ULAN: fill any remaining ULAN IDs
  D  [editorial]    — Manual: add bios/ratings/tags to make_enriched.py, then proceed
  E  merge          — Validate + merge enriched.json → sculptors.json
  F  check_images   — Wikidata P18: list Wikimedia Commons portraits available
  G  check_licenses — Commons API: verify CC license + photographer credit per portrait
  H  apply_avatars  — Write verified avatar URLs + avatar_credit into sculptors.json

Usage:
  python run.py                    # full run — pauses at stage D for editorial work
  python run.py --from E           # resume from stage E (after editorial step is done)
  python run.py --to C             # run stages A–C only
  python run.py --stages F G H     # run a specific subset of stages
"""

import argparse
import subprocess
import sys
import textwrap
from pathlib import Path

HERE   = Path(__file__).parent
PYTHON = sys.executable

STAGE_ORDER = ["A", "B", "C", "D", "E", "F", "G", "H"]

STAGE_LABELS = {
    "A": "wikidata_fetch   — Wikidata SPARQL metadata",
    "B": "moma_fetch       — MoMA CC0 artworks",
    "C": "ulan_fetch       — Getty ULAN IDs",
    "D": "[editorial]      — Add bios / tags / ratings to make_enriched.py",
    "E": "merge            — Merge enriched.json into sculptors.json",
    "F": "check_images     — Wikidata P18 portrait availability",
    "G": "check_licenses   — Wikimedia Commons license verification",
    "H": "apply_avatars    — Write avatar URLs + credits into sculptors.json",
}

STAGE_SCRIPTS: dict[str, tuple[str, list[str]]] = {
    "A": ("wikidata_fetch.py", []),
    "B": ("moma_fetch.py",     []),
    "C": ("ulan_fetch.py",     []),
    "E": ("merge.py",          ["--write"]),
    "F": ("check_images.py",   []),
    "G": ("check_licenses.py", []),
    "H": ("apply_avatars.py",  ["--write"]),
}

EDITORIAL_INSTRUCTIONS = textwrap.dedent("""
    Before continuing, add editorial metadata for each new artist in make_enriched.py:

      1. Open   pipeline/make_enriched.py
      2. Add an entry to the `editorial` dict keyed by Wikidata QID:

           "QXXXXXXX": {
               "country":   "...",
               "city":      "...",
               "bio":       "One-paragraph artist bio.",
               "tags":      ["Tag1", "Tag2"],
               "themes":    ["Theme1", "Theme2"],
               "materials": ["Bronze", "Clay"],
               "rating":    8,       # 1–10
               "mould":     True,    # include only if artist casts multiples
           },

      3. Save make_enriched.py.
      4. Review output/wikidata_raw.json to confirm the QIDs match.
      5. Press Enter here — make_enriched.py will run and write output/enriched.json.
      6. Inspect enriched.json before allowing Stage E to proceed.

    Press Enter when ready, or Ctrl-C to abort.
""").strip()


def hr(char: str = "─", width: int = 62) -> None:
    print(char * width)


def banner(stage: str) -> None:
    hr()
    print(f"  Stage {stage}: {STAGE_LABELS[stage]}")
    hr()


def run_script(stage: str, script: str, extra: list[str]) -> bool:
    banner(stage)
    result = subprocess.run(
        [PYTHON, HERE / script] + extra,
        cwd=HERE,
    )
    if result.returncode != 0:
        print(f"\n  ERROR: stage {stage} exited with code {result.returncode}. Stopping.")
        print(f"  Fix the error and resume with:  python run.py --from {stage}")
        return False
    return True


def run_editorial() -> bool:
    banner("D")
    print(EDITORIAL_INSTRUCTIONS)
    try:
        input("\n  > ")
    except KeyboardInterrupt:
        print("\n\n  Aborted.")
        return False

    print()
    result = subprocess.run([PYTHON, HERE / "make_enriched.py"], cwd=HERE)
    if result.returncode != 0:
        print("\n  ERROR: make_enriched.py failed.")
        print("  Fix the error and resume with:  python run.py --from D")
        return False

    print("\n  Inspect output/enriched.json, then run:  python run.py --from E")
    return True


def resolve_stages(args: argparse.Namespace) -> list[str]:
    if args.stages:
        stages = [s.upper() for s in args.stages]
        unknown = [s for s in stages if s not in STAGE_ORDER]
        if unknown:
            raise SystemExit(f"Unknown stage(s): {', '.join(unknown)}")
        return stages

    start = STAGE_ORDER.index(args.from_stage.upper()) if args.from_stage else 0
    end   = STAGE_ORDER.index(args.to_stage.upper()) + 1 if args.to_stage else len(STAGE_ORDER)
    return STAGE_ORDER[start:end]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lisculpt artist-batch pipeline runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Stages: A B C D E F G H"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--from",   dest="from_stage", metavar="STAGE",
                       help="Start from this stage (default: A)")
    group.add_argument("--stages", nargs="+", metavar="STAGE",
                       help="Run only these stages")
    parser.add_argument("--to",    dest="to_stage",   metavar="STAGE",
                        help="Stop after this stage (default: H)")
    args = parser.parse_args()

    try:
        stages = resolve_stages(args)
    except SystemExit as e:
        parser.error(str(e))

    print(f"\n  Lisculpt pipeline — running stages: {' '.join(stages)}\n")

    for stage in stages:
        ok = run_editorial() if stage == "D" else run_script(stage, *STAGE_SCRIPTS[stage])
        if not ok:
            sys.exit(1)
        print()

    hr("═")
    print("  Pipeline complete.")
    hr("═")


if __name__ == "__main__":
    main()
