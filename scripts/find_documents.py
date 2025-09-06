# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "requests",
# ]
# ///

import os
from pathlib import Path
import random
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


URL = "https://www.ris.bka.gv.at/UI/Bund/Bundesnormen/IndexBundesrecht.aspx?TabbedMenuSelection=BundesrechtTab"
DOCUMENT_DIR = Path("documents")


def random_sleep(min_sec=1, max_sec=3, factor=1.0):
    t = random.uniform(min_sec, max_sec)
    t *= factor
    print(f"    Sleeping for {t:.2f}s...")
    time.sleep(t)


def find_xx_xx_links(soup):
    pattern = re.compile(r"^\d{2}/\d{2}")
    return [a["href"] for a in soup.find_all("a", string=pattern) if a.get("href")]


def find_pdf_links(soup):
    return [
        a["href"]
        for a in soup.find_all("a", href=lambda h: h and h.lower().endswith(".pdf"))
    ]


def download_file(url, filename, output_dir=DOCUMENT_DIR):
    output_dir.mkdir(exist_ok=True)
    path = output_dir / filename
    if path.exists():
        print(f"    Already Exists, skipping: {filename}.")
        return
    resp = requests.get(url)
    resp.raise_for_status()
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"    Saved: {filename}")


def get_soup(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def main() -> None:
    soup = get_soup(URL)
    sublinks = find_xx_xx_links(soup)
    print(f"Found {len(sublinks)} candidate links with 'xx/xx' pattern.")

    for link in sublinks:
        assert isinstance(link, str)
        full_url = urljoin(URL, link)
        print(f"\nVisiting: {full_url}")
        try:
            page_soup = get_soup(full_url)
        except Exception as e:
            print(f"    Error fetching {full_url}: {e}")
            continue

        pdf_links = find_pdf_links(page_soup)
        print(f"    Found {len(pdf_links)} PDF(s) on page.")
        for pdf in pdf_links:
            print(pdf)
            pdf_url = urljoin(full_url, pdf)
            fname = os.path.basename(pdf_url)
            download_file(pdf_url, fname)
            random_sleep(1, 3, 0.1)
        random_sleep()


if __name__ == "__main__":
    main()
