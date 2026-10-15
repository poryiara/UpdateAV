"""
Step 1: read the latest posts of a public Telegram channel (t.me/s/<channel>),
extract the VPN configs, rename them to "<flag> <country> Config" and write
them (plain text, one per line) to the file `sub.txt`.

Install:  pip install requests beautifulsoup4
Run:      python update_sub.py
"""

import base64
import json
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

CHANNEL = "SOSkeyNET"
LAST_POSTS = 10          # how many of the latest posts (with configs) to use
OUTPUT_FILE = "sub.txt"  # plain text, one config per line
URL = f"https://t.me/s/{CHANNEL}"

LINK_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:vmess|vless|trojan|ss|hysteria2|hy2|wireguard)://[^\s<>\"']+"
)
FLAG_RE = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")

COUNTRIES = {
    "US": "United States", "CA": "Canada", "DE": "Germany", "NL": "Netherlands",
    "GB": "United Kingdom", "FR": "France", "IT": "Italy", "RU": "Russia",
    "TR": "Turkey", "IR": "Iran", "FI": "Finland", "SE": "Sweden",
    "SG": "Singapore", "JP": "Japan", "HK": "Hong Kong", "EE": "Estonia",
    "LV": "Latvia", "LT": "Lithuania", "MD": "Moldova", "BG": "Bulgaria",
    "RO": "Romania", "AU": "Australia", "BE": "Belgium", "CH": "Switzerland",
    "AE": "United Arab Emirates", "KR": "South Korea", "TW": "Taiwan",
    "IN": "India", "PL": "Poland", "ES": "Spain", "UA": "Ukraine",
    "CZ": "Czechia", "AT": "Austria", "NO": "Norway", "DK": "Denmark",
    "IE": "Ireland", "PT": "Portugal", "BR": "Brazil", "IL": "Israel",
    "KZ": "Kazakhstan", "AM": "Armenia", "AZ": "Azerbaijan", "GE": "Georgia",
    "SA": "Saudi Arabia", "CN": "China", "HU": "Hungary", "RS": "Serbia",
    "GR": "Greece", "LU": "Luxembourg", "IS": "Iceland", "CY": "Cyprus",
    "MX": "Mexico", "AR": "Argentina", "ZA": "South Africa", "TH": "Thailand",
    "VN": "Vietnam", "ID": "Indonesia", "MY": "Malaysia", "PH": "Philippines",
    "BY": "Belarus", "SK": "Slovakia", "SI": "Slovenia", "HR": "Croatia",
}


def make_name(old_name: str) -> str:
    """Build '<flag> <country> Config' from the flag found in the old name."""
    m = FLAG_RE.search(old_name)
    if not m:
        return "🌍 Unknown Config"
    flag = m.group(0)
    code = "".join(chr(ord(c) - 0x1F1E6 + ord("A")) for c in flag)
    return f"{flag} {COUNTRIES.get(code, code)} Config"


def rename_vmess(link: str) -> str:
    payload = link[len("vmess://"):].strip()
    try:
        raw = base64.b64decode(payload + "=" * (-len(payload) % 4))
        data = json.loads(raw.decode("utf-8"))
        data["ps"] = make_name(str(data.get("ps", "")))
        new = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        return "vmess://" + base64.b64encode(new.encode("utf-8")).decode()
    except Exception:
        return link  # leave it untouched if it can't be parsed


def rename_link(link: str) -> str:
    if link.startswith("vmess://"):
        return rename_vmess(link)
    base, _, fragment = link.partition("#")
    name = make_name(urllib.parse.unquote(fragment))
    return f"{base}#{urllib.parse.quote(name)}"


def fetch_configs() -> list[str]:
    resp = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    posts = []
    for msg in soup.select("div.tgme_widget_message_wrap"):
        text_el = msg.select_one("div.tgme_widget_message_text")
        if not text_el:
            continue
        links = LINK_RE.findall(text_el.get_text("\n"))
        if links:
            posts.append(links)

    latest = posts[-LAST_POSTS:]          # the page lists oldest -> newest
    configs = []
    for links in reversed(latest):        # newest post first
        configs.extend(rename_link(l) for l in links)
    return configs


def main() -> None:
    configs = fetch_configs()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(configs) + "\n")
    print(f"Wrote {len(configs)} configs to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
