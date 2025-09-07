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
from typing import cast
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


URL = "https://www.ris.bka.gv.at/UI/Bund/Bundesnormen/IndexBundesrecht.aspx?TabbedMenuSelection=BundesrechtTab"
DOCUMENT_DIR = Path("documents")
XX_XX_PATTERN = re.compile(r"^\d{2}/\d{2}")
PDF_PATTERN = re.compile(r"\.pdf$")


def random_sleep(min_sec=1, max_sec=3, factor=1.0):
    t = random.uniform(min_sec, max_sec)
    t *= factor
    print(f"    Sleeping for {t:.2f}s...")
    time.sleep(t)


def find_xx_xx_links(soup: BeautifulSoup) -> list[str]:
    results: list[str] = []
    for element in soup.find_all("a", string=XX_XX_PATTERN):
        if not isinstance(element, Tag):
            continue
        if not element.get("href"):
            continue
        results.append(str(element["href"]))
    return results


def find_first_pdf_link(soup: BeautifulSoup) -> str | None:
    link: Tag = cast(Tag, soup.find_next("a"))
    while link and not link["href"]:
        link = cast(Tag, link.find_next("a"))
    return str(link.get("href")) if link else None


def find_metadata_and_follow_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Find metadata PDF and the link that follows right after."""
    results = []
    for element in soup.find_all("a", href=lambda h: h and PDF_PATTERN.search(h)):
        if not cast(Tag, element).get("href"):
            continue
        print(element)
        link: Tag = cast(Tag, element.find_next("a"))
        while link and not link.get("href"):
            link = cast(Tag, link.find_next("a"))
            print(f"    {link}")
        if link and link.get("href"):
            results.append((element.get_text(strip=True), link["href"]))
    print("")
    return results


def download_file(url, filename, output_dir=DOCUMENT_DIR):
    output_dir.mkdir(exist_ok=True)
    path = output_dir / filename
    if path.exists():
        print(f"    Already Exists, skipping: {filename}.")
        return
    resp = requests.get(url)
    resp.raise_for_status()

    if len(str(path)) > 55:
        path = f"{str(path)[:50]}.pdf"
    with open(path, "wb") as f:
        f.write(resp.content)
    print(f"    Saved: {filename}")


def get_soup(url) -> BeautifulSoup:
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

        meta_links = find_metadata_and_follow_links(page_soup)
        print(f"found {len(meta_links)} metadata links")

        for meta_text, follow_href in meta_links:
            law_page_url = urljoin(full_url, follow_href)
            print(f"{law_page_url}")

            try:
                law_soup = get_soup(law_page_url)
            except Exception as e:
                print(f"{e}")
                continue

            pdf_link = find_first_pdf_link(law_soup)
            pdf_url = urljoin(full_url, pdf_link)
            fname = os.path.basename(pdf_url)
            download_file(pdf_url, fname)
            random_sleep()
        random_sleep()


if __name__ == "__main__":
    main()
