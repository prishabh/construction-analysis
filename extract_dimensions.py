import os
import argparse
import json
from utils.pdf_converter import convert_pdf_to_images
from utils.ocr_helpers import ocr_image
from utils.llm_cleaner_ollama import clean_dimensions_with_mistral
from collections import Counter
import re
from fractions import Fraction

def normalize_and_filter_dimensions(raw_list):
    dimensions = []

    for dim in raw_list:
        original = dim
        dim = dim.strip()
        dim = dim.replace("’", "'").replace("‘", "'").replace("′", "'")
        dim = dim.replace("”", '"').replace("“", '"').replace("″", '"')
        dim = dim.replace("—", "-").replace("–", "-")

        # Remove trailing junk letters
        dim = re.sub(r"[a-zA-Z]", "", dim)
        dim = re.sub(r"\s+", "", dim)

        # Match fractional: 19'9 1/2"
        match = re.match(r"^(\d{1,3})'(\d{1,2})(?:\s*(\d+/\d+))?\"?$", dim)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2)) if match.group(2) else 0
            fraction = match.group(3)

            if feet == 0 and inches < 6:
                continue

            total_inches = inches
            if fraction:
                try:
                    total_inches += float(Fraction(fraction))
                except ZeroDivisionError:
                    continue

            if isinstance(total_inches, float) and not total_inches.is_integer():
                formatted = f"{feet}'{total_inches:.2f}\""
            else:
                formatted = f"{feet}'{int(total_inches)}\""
            dimensions.append(formatted)
            continue

        # Match decimal: 17'7.01"
        match_dec = re.match(r"^(\d{1,3})'(\d{1,2}\.\d+)\"?$", dim)
        if match_dec:
            feet = int(match_dec.group(1))
            decimal_inches = float(match_dec.group(2))
            if feet == 0 and decimal_inches < 6:
                continue
            formatted = f"{feet}'{decimal_inches:.2f}\""
            dimensions.append(formatted)
            continue

        # Match basic: 10'6"
        match_basic = re.match(r"^(\d{1,3})'(\d{1,2})\"$", dim)
        if match_basic:
            feet = int(match_basic.group(1))
            inches = int(match_basic.group(2))
            if feet == 0 and inches < 6:
                continue
            formatted = f"{feet}'{inches}\""
            dimensions.append(formatted)
            continue

    count = Counter(dimensions)
    return sorted(set([x for x in dimensions if count[x] < 5]), key=lambda x: (int(x.split("'")[0]), x))


def process_pdf(pdf_path, output_dir):
    image_paths = convert_pdf_to_images(pdf_path, output_dir)

    for i, image_path in enumerate(image_paths):
        print(f"\n📄 Processing page {i+1} as {image_path}")
        raw_text = ocr_image(image_path)
        print(f"[DEBUG OCR TEXT PAGE {i+1}]:\n{raw_text[:500]}")
        raw_dims = clean_dimensions_with_mistral(raw_text)
        print(f"[DEBUG RAW DIMENSIONS PAGE {i+1}]: {raw_dims}")
        final_dims = normalize_and_filter_dimensions(raw_dims)
        print(f"[DEBUG FINAL DIMENSIONS PAGE {i+1}]: {final_dims}")

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
