import json
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
import datetime

def retrain():
    LOG_FILE = "retrain_log.jsonl"
    FEEDBACK_FILE = "feedback.jsonl"
    ITEMS_FILE = "items_with_embeddings.json"

    # Load items for embedding lookup
    with open(ITEMS_FILE, "r") as f:
        items = json.load(f)
    item_map = {item["id"]: item for item in items}

    def load_feedback(path):
        X, y = [], []

        with open(path, "r") as f:
            for line in f:
                entry = json.loads(line.strip())

                price_diff = abs(entry["replacement_price"] - entry["original_price"])
                rating_diff = abs(entry["replacement_rating"] - entry["original_rating"])
                has_rating = 1 if entry["original_rating"] > 0 and entry["replacement_rating"] > 0 else 0

                # Get embeddings
                orig = item_map.get(entry["original_id"])
                repl = item_map.get(entry["replacement_id"])
                if not orig or not repl:
                    continue

                vec1 = np.array(orig.get("embedding"))
                vec2 = np.array(repl.get("embedding"))

                if vec1 is None or vec2 is None:
                    continue

                similarity = cosine_similarity([vec1], [vec2])[0][0]

                X.append([price_diff, rating_diff, has_rating, similarity])
                y.append(entry["score"])

        return np.array(X), np.array(y)

    # Load and train
    X, y = load_feedback(FEEDBACK_FILE)
    print(f"📊 Training on {len(X)} samples")

    if len(X) < 5:
        print("⚠️ Not enough data to retrain.")
        exit()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("✅ Model trained")
    print(f"MSE: {mse:.2f}")
    print(f"R² Score: {r2:.2f}")

    joblib.dump(model, "replacement_model.pkl")
    print("📦 Saved to replacement_model.pkl")

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "num_samples": len(X),
        "mse": mse,
        "r2": r2,
        "features": ["price_diff", "rating_diff", "has_rating", "semantic_similarity"],
        "model_path": "replacement_model.pkl"
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print("📝 Retrain log saved")
