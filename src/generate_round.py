import json
import random

# Load cleaned items
with open("cleaned_items.json", "r") as f:
    items = json.load(f)

# Group items by subcategory for quick replacement lookup
from collections import defaultdict
by_subcat = defaultdict(list)
for item in items:
    by_subcat[item["subcategory"]].append(item)

# Function to create a round
def generate_game_round(cart_size=4, unavailable_count=2):
    cart = random.sample(items, cart_size)
    unavailable_items = random.sample(cart, min(unavailable_count, cart_size))

    round_data = {
        "cart": [],
        "replacements": {}
    }

    for item in cart:
        item_data = {
            "id": item["id"],
            "title": item["title"],
            "subcategory": item["subcategory"],
            "price": item["price"],
            "rating": item["rating"],
            "unavailable": item in unavailable_items
        }
        round_data["cart"].append(item_data)

        # If unavailable, generate replacement options
        if item in unavailable_items:
            options = [
                alt for alt in by_subcat[item["subcategory"]]
                if alt["id"] != item["id"]
            ]
            sampled = random.sample(options, min(4, len(options)))
            round_data["replacements"][item["id"]] = sampled

    return round_data

# Example round
game_round = generate_game_round()
print(json.dumps(game_round, indent=2))
