"""Apply Wikimedia Commons portrait images and credits to sculptors.json.

Sets avatar and avatar_credit for the 12 CC-licensed portraits found by
check_images.py and verified by check_licenses.py. Also adds avatar_credit: null
to all artists that lack the field (schema migration for existing records).

Usage:
    python apply_avatars.py           # dry run — shows what would change
    python apply_avatars.py --write   # update sculptors.json
"""

import argparse
import json
from pathlib import Path

SCULPTORS_PATH = Path(__file__).parent.parent / "Lisculpt" / "sculptors.json"

# keyed by wikidata_qid; (avatar_url, photographer_credit)
AVATARS: dict[str, tuple[str, str]] = {
    "Q447300":   ("https://commons.wikimedia.org/wiki/Special:FilePath/Kiki%20Smith%208229.jpg",                                                                                                         "Nina Subin"),
    "Q19800726": ("https://commons.wikimedia.org/wiki/Special:FilePath/Ibrahim%20Mahama%20at%20Art%20Basel%202025%20in%20Basel%2001.jpg",                                                                "Bea Phi"),
    "Q3033213":  ("https://commons.wikimedia.org/wiki/Special:FilePath/Do%20Ho%20Suh%20and%20Eitaro%20Ogawa%20%28cropped%29.jpg",                                                                       "Joyce at STPI Gallery"),
    "Q19509449": ("https://commons.wikimedia.org/wiki/Special:FilePath/The%20Jewish%20Museum%27s%20Wikipedia%20Edit-a-Thon%2016%20%28cropped%29.jpg",                                                   "Sara Wasserman"),
    "Q7901287":  ("https://commons.wikimedia.org/wiki/Special:FilePath/Ursula%20von%20Rydingsvard.jpg",                                                                                                 "Ursula von Rydingsvard"),
    "Q1578729":  ("https://commons.wikimedia.org/wiki/Special:FilePath/Oliver%20Mark%20-%20Alicja%20Kwade%2C%20Berlin%202014.jpg",                                                                      "Oliver Mark"),
    "Q7777257":  ("https://commons.wikimedia.org/wiki/Special:FilePath/Unleashing%20Entrepreneurial%20Innovation%20with%20Stanford%20University%20Theaster%20Gates.jpg",                                "World Economic Forum"),
    "Q2900658":  ("https://commons.wikimedia.org/wiki/Special:FilePath/Bharti%20Kher.gif",                                                                                                              "Caroline Perrotin"),
    "Q19998132": ("https://commons.wikimedia.org/wiki/Special:FilePath/Carlos%20Bunga%20i%20Antonio%20Gagliano%20durant%20l%E2%80%99enregistrament%20d%E2%80%99un%20nou%20FONS%20%C3%80UDIO.jpg",      "MACBA"),
    "Q273696":   ("https://commons.wikimedia.org/wiki/Special:FilePath/IVAM%20-%20Mona%20Hatoum.jpg",                                                                                                   "Miguel Lorenzo"),
    "Q16200002": ("https://commons.wikimedia.org/wiki/Special:FilePath/Simone%20Leigh%202%20%28cropped%29.jpg",                                                                                         "Tiffany I. Smith"),
    "Q43387704": ("https://commons.wikimedia.org/wiki/Special:FilePath/Leila%20Babirye.jpg",                                                                                                            "Sunshine Fionah Komusana"),
}


def insert_avatar_credit(artist: dict, credit: str | None) -> dict:
    """Return artist dict with avatar_credit placed immediately after avatar."""
    if "avatar_credit" in artist:
        return artist
    result = {}
    for key, value in artist.items():
        result[key] = value
        if key == "avatar":
            result["avatar_credit"] = credit
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true",
                        help="Write changes to sculptors.json (default: dry run)")
    args = parser.parse_args()

    data = json.loads(SCULPTORS_PATH.read_text(encoding="utf-8"))
    artists = data["artists"]

    updated = []
    for artist in artists:
        qid = artist.get("wikidata_qid")
        if qid in AVATARS:
            avatar_url, credit = AVATARS[qid]
            patched = insert_avatar_credit(artist, credit)
            if patched.get("avatar") != avatar_url or patched.get("avatar_credit") != credit:
                print(f"  SET  {artist['name']}: avatar + credit='{credit}'")
            else:
                print(f"  OK   {artist['name']}: already set")
            patched["avatar"] = avatar_url
            patched["avatar_credit"] = credit
            updated.append(patched)
        else:
            patched = insert_avatar_credit(artist, artist.get("avatar_credit"))
            if "avatar_credit" not in artist:
                print(f"  ADD  {artist['name']}: avatar_credit=null (schema migration)")
            updated.append(patched)

    if args.write:
        data["artists"] = updated
        output = json.dumps(data, indent=2, ensure_ascii=False)
        json.loads(output)  # validate before writing
        SCULPTORS_PATH.write_text(output + "\n", encoding="utf-8")
        print(f"\nWrote {SCULPTORS_PATH}")
    else:
        print("\nDry run — pass --write to apply changes.")


if __name__ == "__main__":
    main()
