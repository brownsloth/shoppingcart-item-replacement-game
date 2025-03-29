from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer("all-MiniLM-L6-v2")  # fast and small

with open("cleaned_items.json", "r") as f:
    items = json.load(f)

for item in items:
    desc = item.get("product_description") or item["title"]
    item["embedding"] = model.encode(desc).tolist()

with open("items_with_embeddings.json", "w") as f:
    json.dump(items, f, indent=2)

print("✅ Saved embeddings to items_with_embeddings.json")
