import pandas as pd
import json
import uuid
import re
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Load raw CSV (change filename if needed)
df = pd.read_csv("GroceryDataset.csv")

# Drop nulls in critical columns
df = df.dropna(subset=["Title", "Sub Category", "Price", "Product Description"])

# Fill optional fields if missing
df["Rating"] = df["Rating"].fillna(0)
df["Discount"] = df["Discount"].fillna(0)
df["Feature"] = df["Feature"].fillna("")

# Tokenizer for features + description
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    words = text.split()
    return [w for w in words if w not in ENGLISH_STOP_WORDS and len(w) > 2]

def parse_price(value):
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace(",", "")
    try:
        return float(value)
    except:
        return None  # or 0.0 if you want to keep bad values

def parse_discount(value):
    if isinstance(value, str):
        value = value.strip().replace("%", "")
    try:
        return float(value)
    except:
        return 0.0

import re

def extract_rating(text):
    if isinstance(text, str):
        match = re.search(r"(\d\.\d)", text)
        if match:
            return float(match.group(1))
    try:
        return float(text)
    except:
        return 0.0


# Build item dicts
items = []
for _, row in df.iterrows():
    item = {
        "id": str(uuid.uuid4())[:8],
        "title": row["Title"].strip(),
        "subcategory": row["Sub Category"].strip(),
        "price": parse_price(row["Price"]),
        "discount": parse_discount(row["Discount"]),
        "rating": extract_rating(row["Rating"]),
        "features": tokenize(row["Feature"]),
        "description": row["Product Description"].strip(),
        "tokens": tokenize(row["Product Description"] + " " + row["Feature"])
    }
    items.append(item)

# Save cleaned file
with open("cleaned_items.json", "w") as f:
    json.dump(items, f, indent=2)

print(f"✅ Processed {len(items)} items and saved to cleaned_items.json")
