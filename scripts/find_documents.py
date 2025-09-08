# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "beautifulsoup4",
#     "requests",
# ]
# ///

import hashlib
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
    t = random.uniform(min_sec, max_sec) * factor
    print(f"    Sleeping for {t:.2f}s...")
    time.sleep(t)


def sanitize_filename(text: str, max_length: int = 120) -> str:
    """Make a safe filename, ensure .pdf extension, and shorten with hash if too long."""
    text = (text or "document").strip()
    text = text.replace("/", "-")
    text = re.sub(r"[^\w\-.() ]+", "_", text)
    text = text.replace("20_", "_")
    if not text.lower().endswith(".pdf"):
        text = f"{text}.pdf"

    if len(text) <= max_length:
        return text

    base, ext = text.rsplit(".", 1)
    hash_suffix = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    # reserve room for "_" + hash + "." + ext
    keep = max_length - (1 + len(hash_suffix) + 1 + len(ext))
    if keep <= 0:
        # fallback: use hash only
        return f"{hash_suffix}.{ext}"
    short_base = base[:keep]
    # TODO: make text utf-8
    return f"{short_base}_{hash_suffix}.{ext}"


def find_xx_xx_links(soup: BeautifulSoup) -> list[str]:
    results: list[str] = []
    for element in soup.find_all("a", string=XX_XX_PATTERN):
        if not isinstance(element, Tag):
            continue
        href = element.get("href")
        if not href:
            continue
        results.append(str(href))
    return results


def find_first_pdf_link(soup: BeautifulSoup) -> tuple[str, str] | None:
    """
    On a law page, find the first PDF anchor (likely the real law text).
    Return (text, href) or None.
    """
    a = soup.find("a", href=lambda h: h and PDF_PATTERN.search(h))  # pyright: ignore
    if not a or not isinstance(a, Tag):
        return None
    href = a.get("href")
    if not href:
        return None
    text = a.get_text(strip=True) or os.path.basename(str(href))
    return text, str(href)


def find_metadata_and_follow_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Find metadata PDF and the link that follows right after."""
    results = []
    for element in soup.find_all("a", href=lambda h: h and PDF_PATTERN.search(h)):  # pyright: ignore
        if not isinstance(element, Tag):
            continue
        meta_href = element.get("href")
        if not meta_href:
            continue
        print(element)
        meta_text = element.get_text(strip=True) or os.path.basename(str(meta_href))
        follow_href: str | None = None
        for next_a in element.find_all_next("a"):
            if not isinstance(next_a, Tag):
                continue
            nh = next_a.get("href")
            if nh:
                follow_href = str(nh)
                break

        if follow_href:
            results.append((meta_text, follow_href))
    return results


def download_file(url: str, filename: str, output_dir=DOCUMENT_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = sanitize_filename(filename, max_length=120)
    path = output_dir / filename
    if path.exists():
        print(f"    Already Exists, skipping: {filename}.")
        return
    with requests.get(url, stream=True) as resp:
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
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

            pdf_tuple = find_first_pdf_link(law_soup)
            if not pdf_tuple:
                print(" No PDF found")
                continue
            pdf_text, pdf_href = pdf_tuple
            pdf_url = urljoin(law_page_url, pdf_href)
            fname = pdf_text
            try:
                download_file(pdf_url, fname)
            except Exception as e:
                print(f"{e}")
            random_sleep()
        random_sleep()


if __name__ == "__main__":
    main()
