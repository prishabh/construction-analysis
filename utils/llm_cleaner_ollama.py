import re
import json
import requests
import time
from fractions import Fraction

def normalize_dimension(text):
    text = text.strip()
    text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
    text = text.replace('–', '-').replace('—', '-').replace('‐', '-')
    text = re.sub(r'[^\x00-\x7F]', '', text)  # remove non-ASCII
    text = re.sub(r'[^\d\'\"\/\s.-]', '', text)  # keep only dimension chars
    text = re.sub(r'\s+', '', text)
    return text

def is_valid_dimension(s):
    s = s.strip().replace("’", "'").replace("”", '"').replace("“", '"')
    if not s.endswith('"'):
        s += '"'

    # Match feet and inches optionally with fraction
    match = re.match(r"^(\d{1,3})'(\d{1,2})(\.\d{1,2})?\"$", s)
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        if feet == 0 and inches < 6:
            return False
        return True
    return False

def clean_and_normalize(parsed_list):
    dimensions = []
    for dim in parsed_list:
        dim = normalize_dimension(dim)
        dim = dim.replace('"', '')  # remove trailing quote for parsing
        match = re.match(r"^(\d+)'(\d{1,2})(?:\s*(\d+/\d+))?$", dim)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            frac = match.group(3)
            if frac:
                try:
                    val = Fraction(frac)
                    if val < Fraction(1, 8):  # skip tiny noise fractions
                        frac = None
                except Exception:
                    frac = None
            if frac:
                total_inches = inches + float(Fraction(frac))
                dimensions.append(f"{feet}'{total_inches:.2f}\"")
            else:
                dimensions.append(f"{feet}'{inches}\"")
            continue

        match_basic = re.match(r"^(\d+)'(\d{1,2})$", dim)
        if match_basic:
            dimensions.append(f"{match_basic.group(1)}'{match_basic.group(2)}\"")
            continue
    return dimensions

def fallback_regex_extract(text):
    raw = re.findall(r"\d{1,3}['’][-\d\s/]+", text)
    results = []
    for r in raw:
        r = r.replace("’", "'")
        if "'" not in r:
            continue
        parts = re.split(r"['\"]", r)
        if len(parts) < 2:
            continue
        feet = re.sub(r"[^\d]", "", parts[0])
        rest = re.sub(r"[^\d/]", "", parts[1])
        if not feet.isdigit():
            continue
        try:
            inches = 0
            if rest:
                if '/' in rest:
                    inches += float(Fraction(rest))
                else:
                    inches += int(rest)
            if int(feet) == 0 and inches < 6:
                continue
            if inches % 1 == 0:
                results.append(f"{feet}'{int(inches)}\"")
            else:
                results.append(f"{feet}'{inches:.2f}\"")
        except:
            continue
    return results

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

    for attempt in range(2):
        try:
            response = requests.post("http://host.docker.internal:11434/api/generate", json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                print(f"[LLM ERROR] Ollama returned {response.status_code}")
                break

            raw = response.json().get("response", "").strip()
            print(f"\n[LLM RAW OUTPUT]:\n{raw}")

            raw = re.sub(r"```(?:json)?", "", raw).strip("` \n")
            raw = raw.replace("“", "\"").replace("”", "\"").replace("''", "\"").replace("'", "'").replace('""', '"')

            match = re.search(r'\[\s*(?:"[^"]*"\s*,?\s*)+\]', raw)
            if match:
                try:
                    candidates = json.loads(match.group(0))
                    candidates = [normalize_dimension(s) for s in candidates]
                    parsed = clean_and_normalize(candidates)
                    if parsed:
                        return parsed
                    else:
                        print("[LLM ERROR] Valid list parsed but no usable dimensions found.")
                except json.JSONDecodeError as e:
                    print(f"[LLM ERROR] JSON parsing failed: {e}. Attempting manual list recovery...")
                    stripped = re.findall(r'"(.*?)"', raw)
                    parsed = clean_and_normalize(stripped)
                    if parsed:
                        return parsed
        except requests.exceptions.ReadTimeout:
            print(f"[LLM ERROR] Timeout on attempt {attempt+1}. Retrying...")
            time.sleep(1)
        except Exception as e:
            print(f"[LLM ERROR] Ollama call failed: {e}")
            break

    print("[FALLBACK] Using regex-based extraction")
    return fallback_regex_extract(ocr_text)
