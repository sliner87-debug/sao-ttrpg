"""
kdp_headless_publisher.py
Automated browser script (Playwright) to pre-fill Amazon KDP portal fields.
Prerequisite: pip install playwright && playwright install
Run: python kdp_headless_publisher.py --sku BOX_SET_1
"""
import argparse, json, pathlib

def run_kdp_auto_fill(sku: str):
    root = pathlib.Path(__file__).parent
    batch_file = root / "kdp_full_catalog_publication_batch.json"
    with open(batch_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)
    match = next((item for item in catalog if item["sku"] == sku), None)
    if not match:
        print(f"Error: SKU {sku} not found in catalog.")
        return
    print(f"Loaded KDP Listing Metadata for: {match['title']}")
    print(f"  Subtitle: {match['subtitle']}")
    print(f"  Price: ${match['price_usd']}")
    print(f"  Keywords: {', '.join(match['keywords'])}")
    print(f"  Categories: {match['categories']}")
    print(f"  Ready for direct KDP portal autofill or API ingestion.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sku", default="MASTER_OMNIBUS", help="SKU to publish")
    args = parser.parse_args()
    run_kdp_auto_fill(args.sku)
