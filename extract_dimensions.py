import os
import argparse
import json
from utils.pdf_converter import convert_pdf_to_images
from utils.ocr_helpers import ocr_image
from utils.llm_cleaner_ollama import clean_dimensions_with_mistral
from collections import Counter

def normalize_and_filter_dimensions(raw_list):
    import re
    cleaned = []

    for item in raw_list:
        item = item.strip()
        item = re.sub(r'[^0-9\'"]+', '', item)  # strip garbage
        if re.match(r"^\d{1,3}'$", item):
            item += '0"'
        elif re.match(r"^\d{1,3}'\d{1,2}$", item):
            item += '"'
        item = item.replace("''", "\"").replace('""', "\"")

        if re.match(r"^\d{1,3}'\d{0,2}\"$", item):
            cleaned.append(item)

    # Remove repeated values (e.g., too many "1'1")
    deduped = []
    freq = Counter(cleaned)
    for val in cleaned:
        if freq[val] < 5:  # filter excessive duplicates
            deduped.append(val)

    return deduped

def process_pdf(pdf_path, output_dir):
    image_paths = convert_pdf_to_images(pdf_path, output_dir)

    for i, image_path in enumerate(image_paths):
        print(f"\n📄 Processing page {i+1} as {image_path}")
        raw_text = ocr_image(image_path)
        raw_dims = clean_dimensions_with_mistral(raw_text)
        final_dims = normalize_and_filter_dimensions(raw_dims)

        output_path = os.path.join(output_dir, f"page_{i+1}_output.json")
        with open(output_path, "w") as f:
            json.dump({"dimensions": final_dims}, f, indent=2)
        print(f"✅ Saved {len(final_dims)} dimensions to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    process_pdf(args.pdf, args.output)
