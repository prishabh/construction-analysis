import os
import json

def merge_output_files(output_dir):
    result = {}
    for fname in sorted(os.listdir(output_dir)):
        if fname.endswith(".json") and "page_" in fname:
            page_num = fname.split("_")[1]
            with open(os.path.join(output_dir, fname)) as f:
                data = json.load(f)
            result[f"page_{page_num}"] = data["dimensions"]

    with open(os.path.join(output_dir, "all_dimensions.json"), "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ Merged output saved to {output_dir}/all_dimensions.json")

if __name__ == "__main__":
    merge_output_files("output")
