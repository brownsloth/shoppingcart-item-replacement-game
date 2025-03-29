from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import random
from collections import defaultdict
from pydantic import BaseModel
from typing import List
from pydantic import BaseModel
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity
import os
import time
from apscheduler.schedulers.background import BackgroundScheduler
from train_replacement_model import retrain

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(retrain, 'interval', minutes=1000)
    scheduler.start()
    print("⏰ Scheduled retraining every 1000 minutes")

MODEL_PATH = "replacement_model.pkl"
model = None
model_last_loaded = 0
MODEL_CHECK_INTERVAL = 3  # seconds

def load_model_if_updated():
    global model, model_last_loaded
    try:
        modified = os.path.getmtime(MODEL_PATH)
        if (model is None) or (time.time() - model_last_loaded > MODEL_CHECK_INTERVAL and modified > model_last_loaded):
            model = joblib.load(MODEL_PATH)
            model_last_loaded = modified
            print("🔁 Reloaded model")
    except FileNotFoundError:
        model = None

class PredictionInput(BaseModel):
    original_price: float
    replacement_price: float
    original_rating: float
    replacement_rating: float
    original_id: str
    replacement_id: str

# Feedback model
class FeedbackEntry(BaseModel):
    user_id: str
    original_id: str
    replacement_id: str
    original_price: float
    replacement_price: float
    original_rating: float
    replacement_rating: float
    score: float  # optional but useful

app = FastAPI()
start_scheduler()

#also retrain if feedback.jsonl has grown by N entries
def should_retrain(threshold=50):
    try:
        with open("feedback.jsonl") as f:
            return sum(1 for _ in f) % threshold == 0
    except:
        return False

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your frontend origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load cleaned items
with open("items_with_embeddings.json", "r") as f:
    items = json.load(f)

# Group items by subcategory for replacements
by_subcat = defaultdict(list)
for item in items:
    by_subcat[item["subcategory"]].append(item)

def generate_game_round(cart_size=4, unavailable_count=2):
    cart = random.sample(items, cart_size)

    valid_unavailables = []
    for item in cart:
        options = [
            alt for alt in by_subcat[item["subcategory"]]
            if alt["id"] != item["id"]
        ]
        if len(options) >= 1:
            valid_unavailables.append(item)

    # Pick up to `unavailable_count` items with valid replacements
    unavailable_items = random.sample(valid_unavailables, min(unavailable_count, len(valid_unavailables)))

    round_data = {
        "cart": [],
        "replacements": {}
    }

    for item in cart:
        is_unavailable = item in unavailable_items
        item_data = {
            "id": item["id"],
            "title": item["title"],
            "subcategory": item["subcategory"],
            "price": item["price"],
            "rating": item["rating"],
            "unavailable": is_unavailable
        }
        round_data["cart"].append(item_data)

        if is_unavailable:
            options = [
                alt for alt in by_subcat[item["subcategory"]]
                if alt["id"] != item["id"]
            ]
            # After checking sampled options
            sampled = [alt for alt in by_subcat[item["subcategory"]] if alt["id"] != item["id"]]
            if not sampled:
                continue  # No valid replacements — skip this item

            sampled = random.sample(sampled, min(4, len(sampled)))
            round_data["replacements"][item["id"]] = sampled

    return round_data

@app.get("/generate_round")
def get_game_round():
    return generate_game_round()

@app.post("/log_feedback")
def log_feedback(entry: FeedbackEntry):
    with open("feedback.jsonl", "a") as f:
        f.write(entry.json() + "\n")

    if should_retrain():
        retrain()

    return {"status": "logged"}

@app.post("/predict_score")
def predict_score(payload: PredictionInput):
    load_model_if_updated()
    price_diff = abs(payload.replacement_price - payload.original_price)
    rating_diff = abs(payload.replacement_rating - payload.original_rating)
    has_rating = 1 if payload.original_rating > 0 and payload.replacement_rating > 0 else 0

    # Embedding similarity
    original_item = next((i for i in items if i["id"] == payload.original_id), None)
    replacement_item = next((i for i in items if i["id"] == payload.replacement_id), None)

    similarity = 0.5  # neutral fallback
    if original_item and replacement_item and "embedding" in original_item and "embedding" in replacement_item:
        similarity = float(
            cosine_similarity(
                [original_item["embedding"]],
                [replacement_item["embedding"]]
            )[0][0]
        )

    # If model exists, use it. Else fallback to rule score
    if model:
        features = np.array([[price_diff, rating_diff, has_rating, similarity]])
        score = float(model.predict(features)[0])
    else:
        # Rule-based score approximation
        price_score = max(0, 1 - price_diff / 5)
        rating_score = max(0, 1 - rating_diff / 5)
        score = 50 * price_score + 50 * rating_score

    return {"predicted_score": round(score, 2)}

@app.get("/retrain_logs")
def get_retrain_logs():
    try:
        with open("retrain_log.jsonl", "r") as f:
            logs = [json.loads(line) for line in f]
        return {"logs": logs[::-1]}  # newest first
    except FileNotFoundError:
        return {"logs": []}


