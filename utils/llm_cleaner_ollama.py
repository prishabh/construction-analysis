import requests
import json
import re
import time

def clean_dimensions_with_mistral(ocr_text):
    prompt = f"""
Extract architectural dimensions from the OCR text below. Output only a JSON list of strings, like: ["3'0\"", "12'6\"", "0'8\""]. No markdown, no explanation, no formatting.

OCR text:
{ocr_text}
"""

    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(2):  # retry once
        try:
            response = requests.post("http://host.docker.internal:11434/api/generate", json=payload, headers=headers, timeout=60)

            if response.status_code != 200:
                print(f"[LLM ERROR] Ollama returned {response.status_code}")
                return []

            raw = response.json().get("response", "").strip()
            print(f"\n[LLM RAW OUTPUT]:\n{raw}")

            # Clean up common noise
            raw = re.sub(r"```(?:json)?", "", raw).strip("`")
            raw = raw.replace("“", "\"").replace("”", "\"")
            raw = raw.replace("''", "\"").replace("'", "'")
            raw = raw.replace('""', '"')

            # Find a valid list using regex
            match = re.search(r'\[\s*(?:"[^"]*"\s*,?\s*)+\]', raw)
            if match:
                json_block = match.group(0)
                return json.loads(json_block)

            print("[LLM ERROR] No valid list matched.")
            return []

        except requests.exceptions.ReadTimeout:
            print(f"[LLM ERROR] Timeout on attempt {attempt+1}. Retrying...")
            time.sleep(1)
        except Exception as e:
            print(f"[LLM ERROR] Ollama call failed: {e}")
            return []

    return []
