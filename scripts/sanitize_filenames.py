# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

from pathlib import Path


def main() -> None:
    path = Path("documents")
    pdfs = path.rglob("*.pdf")
    for pdf in pdfs:
        new_name = pdf.name.replace("_20", "_")
        new_path = pdf.with_name(new_name)
        pdf.rename(new_path)


if __name__ == "__main__":
    main()
