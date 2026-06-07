"""Check Wikimedia Commons licenses for the 12 portrait images found by check_images.py.

Queries the Commons imageinfo API for LicenseShortName, LicenseUrl, and Artist
attribution for each file. Prints a summary table and full detail per image.

Usage:
    python check_licenses.py
"""

import json
import re
import time
import urllib.parse
import urllib.request

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "Lisculpt-pipeline/1.0 (https://github.com/guilnunes/Lisculpt)"

PORTRAITS = [
    ("Kiki Smith",             "Q447300",   "http://commons.wikimedia.org/wiki/Special:FilePath/Kiki%20Smith%208229.jpg"),
    ("Ibrahim Mahama",         "Q19800726", "http://commons.wikimedia.org/wiki/Special:FilePath/Ibrahim%20Mahama%20at%20Art%20Basel%202025%20in%20Basel%2001.jpg"),
    ("Do Ho Suh",              "Q3033213",  "http://commons.wikimedia.org/wiki/Special:FilePath/Do%20Ho%20Suh%20and%20Eitaro%20Ogawa%20%28cropped%29.jpg"),
    ("Arlene Shechet",         "Q19509449", "http://commons.wikimedia.org/wiki/Special:FilePath/The%20Jewish%20Museum%27s%20Wikipedia%20Edit-a-Thon%2016%20%28cropped%29.jpg"),
    ("Ursula von Rydingsvard", "Q7901287",  "http://commons.wikimedia.org/wiki/Special:FilePath/Ursula%20von%20Rydingsvard.jpg"),
    ("Alicja Kwade",           "Q1578729",  "http://commons.wikimedia.org/wiki/Special:FilePath/Oliver%20Mark%20-%20Alicja%20Kwade%2C%20Berlin%202014.jpg"),
    ("Theaster Gates",         "Q7777257",  "http://commons.wikimedia.org/wiki/Special:FilePath/Unleashing%20Entrepreneurial%20Innovation%20with%20Stanford%20University%20Theaster%20Gates.jpg"),
    ("Bharti Kher",            "Q2900658",  "http://commons.wikimedia.org/wiki/Special:FilePath/Bharti%20Kher.gif"),
    ("Carlos Bunga",           "Q19998132", "http://commons.wikimedia.org/wiki/Special:FilePath/Carlos%20Bunga%20i%20Antonio%20Gagliano%20durant%20l%E2%80%99enregistrament%20d%E2%80%99un%20nou%20FONS%20%C3%80UDIO.jpg"),
    ("Mona Hatoum",            "Q273696",   "http://commons.wikimedia.org/wiki/Special:FilePath/IVAM%20-%20Mona%20Hatoum.jpg"),
    ("Simone Leigh",           "Q16200002", "http://commons.wikimedia.org/wiki/Special:FilePath/Simone%20Leigh%202%20%28cropped%29.jpg"),
    ("Leilah Babirye",         "Q43387704", "http://commons.wikimedia.org/wiki/Special:FilePath/Leila%20Babirye.jpg"),
]


def filename_from_url(url: str) -> str:
    return urllib.parse.unquote(url.split("Special:FilePath/")[-1])


def fetch_license(filename: str) -> dict:
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "extmetadata",
        "format": "json",
    }
    url = COMMONS_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        imageinfo = page.get("imageinfo", [{}])
        if imageinfo:
            return imageinfo[0].get("extmetadata", {})
    return {}


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def usability(license_short: str) -> str:
    low = license_short.lower()
    if "cc0" in low or "public domain" in low:
        return "YES (no attribution needed)"
    if "cc" in low:
        return "YES (attribution required)"
    if "copyright" in low or "all rights" in low or "fair use" in low:
        return "NO"
    return "CHECK"


def main():
    print("## Wikimedia Commons license check\n")
    print(f"{'Artist':<30} {'License':<22} {'Usable?'}")
    print("-" * 72)

    details = []
    for name, qid, url in PORTRAITS:
        filename = filename_from_url(url)
        try:
            meta = fetch_license(filename)
        except Exception as e:
            print(f"{name:<30} {'ERROR':<22} {e}")
            continue

        license_short = meta.get("LicenseShortName", {}).get("value", "unknown")
        license_url   = meta.get("LicenseUrl",       {}).get("value", "")
        artist_html   = meta.get("Artist",            {}).get("value", "")
        artist        = strip_html(artist_html)

        verdict = usability(license_short)
        print(f"{name:<30} {license_short:<22} {verdict}")
        details.append((name, qid, url, license_short, license_url, artist, verdict))
        time.sleep(0.3)

    print("\n### Attribution detail\n")
    for name, qid, url, lic, lic_url, artist, verdict in details:
        print(f"**{name}** ({qid}) — {lic} — {verdict}")
        if artist:
            print(f"  Credit: {artist}")
        if lic_url:
            print(f"  License: {lic_url}")
        print(f"  File: {url}")
        print()


if __name__ == "__main__":
    main()
