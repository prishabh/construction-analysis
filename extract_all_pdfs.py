import os
import json
from extract_dimensions import process_pdf

def find_all_pdfs(root_dir):
    pdf_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.lower().endswith(".pdf"):
                pdf_files.append(os.path.join(dirpath, file))
    return pdf_files

def relative_output_path(pdf_path, root_input="sample", root_output="output"):
    rel_path = os.path.relpath(pdf_path, root_input)
    rel_path_no_ext = os.path.splitext(rel_path)[0]
    return os.path.join(root_output, rel_path_no_ext)

def merge_page_outputs(output_dir):
    merged = []
    for fname in sorted(os.listdir(output_dir)):
        if fname.startswith("page_") and fname.endswith("_output.json"):
            page_path = os.path.join(output_dir, fname)
            with open(page_path, "r") as f:
                data = json.load(f)
            merged.append(data)

    merged_file = output_dir + ".json"  # output like: output/Chandler Connell/Harris-Connell.json
    os.makedirs(os.path.dirname(merged_file), exist_ok=True)
    with open(merged_file, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"✅ Merged: {merged_file}")

def main():
    pdfs = find_all_pdfs("sample")

    print(f"🔍 Found {len(pdfs)} PDFs.")
    for pdf in pdfs:
        output_dir = relative_output_path(pdf)
        os.makedirs(output_dir, exist_ok=True)

        print(f"\n📄 Processing {pdf} → {output_dir}")
        process_pdf(pdf, output_dir)
        merge_page_outputs(output_dir)

    print("\n🎉 All PDFs processed and merged successfully.")

if __name__ == "__main__":
    main()
