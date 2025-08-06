import re
from rapidfuzz import fuzz

def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text

def match_scripted_response(user_input, qa_data):
    cleaned = normalize(user_input)
    print(f"[🔎 Matching Exact] Input cleaned: {cleaned}")
    for item in qa_data:
        for keyword in item["keywords"]:
            if cleaned == normalize(keyword):
                print(f"[✅ Exact Match Found] → {keyword}")
                return item["answer"], "exact_match"
    return None, None

def fuzzy_match(user_input, qa_data):
    cleaned = normalize(user_input)
    best_score = 0
    best_response = None
    for item in qa_data:
        for keyword in item["keywords"]:
            score = fuzz.partial_ratio(cleaned, normalize(keyword))
            if score > best_score:
                best_score = score
                best_response = item["answer"]
    if best_score >= 88:  # Slightly relaxed threshold
        return best_response, "fuzzy_match"
    return None, None
