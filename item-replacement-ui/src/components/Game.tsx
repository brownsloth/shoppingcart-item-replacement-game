"use client";

import { useEffect, useState } from "react";
import { fetchGameRound } from "@/lib/api";
type Item = {
  id: string;
  title: string;
  subcategory: string;
  price: number;
  rating: number;
  unavailable: boolean;
};

type GameRound = {
  cart: Item[];
  replacements: Record<string, Item[]>;
};

export default function Game() {
  const [round, setRound] = useState<GameRound | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [userId, setUserId] = useState("");

  useEffect(() => {
    let stored = localStorage.getItem("user_id");
    if (!stored) {
      stored = "user_" + Date.now();
      localStorage.setItem("user_id", stored);
    }
    setUserId(stored);
  }, []);

  useEffect(() => {
    fetchGameRound()
      .then(data => {
        console.log("🟢 Game round data:", data);
        setRound(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("❌ Failed to fetch game round", err);
        setLoading(false);
      });
  }, []);


  const handleSelect = (unavailableItemId: string, replacementId: string) => {
    setSelected(prev => ({
      ...prev,
      [unavailableItemId]: replacementId
    }));
  };
  const handleSubmit = async () => {
    if (!round) return;

    let total = 0;
    let count = 0;

    for (const unavailableItem of round.cart.filter(i => i.unavailable)) {
      const selectedId = selected[unavailableItem.id];
      if (!selectedId) continue;

      const options = round.replacements[unavailableItem.id];
      const chosen = options.find(opt => opt.id === selectedId);
      if (!chosen) continue;

      try {
        const response = await fetch("http://localhost:8000/predict_score", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            original_price: unavailableItem.price,
            replacement_price: chosen.price,
            original_rating: unavailableItem.rating,
            replacement_rating: chosen.rating,
            original_id: unavailableItem.id,
            replacement_id: chosen.id
          })
        });

        const data = await response.json();
        const predicted = data.predicted_score || 0;

        total += predicted;
        count += 1;

        // Also log feedback
        const entry = {
          user_id: userId,
          original_id: unavailableItem.id,
          replacement_id: chosen.id,
          original_price: unavailableItem.price,
          replacement_price: chosen.price,
          original_rating: unavailableItem.rating,
          replacement_rating: chosen.rating,
          score: predicted
        };

        fetch("http://localhost:8000/log_feedback", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(entry)
        }).catch(err => console.error("Logging failed", err));
      } catch (err) {
        console.error("Prediction failed", err);
      }
    }

    const avgScore = count > 0 ? total / count : 0;
    setScore(Math.round(avgScore));
    setSubmitted(true);
  };

  if (loading) return <div className="text-center mt-12 text-white">Loading game...</div>;
  if (!round) return <div className="text-red-500 text-center mt-12">Failed to load round.</div>;

  return (
    <div className="max-w-4xl mx-auto mt-8 space-y-8 text-white">
      <h2 className="text-3xl font-bold mb-4">Customer Cart</h2>
      <ul className="space-y-2">
        {round.cart.map(item => (
          <li
            key={item.id}
            className={`p-4 rounded border ${
              item.unavailable ? "bg-red-500/20 border-red-500" : "bg-gray-800 border-gray-600"
            }`}
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-semibold">{item.title}</p>
                <p className="text-sm text-gray-400">
                  Price: {item.price != null ? `$${item.price.toFixed(2)}` : "N/A"} | 
                  Rating: {item.rating != null ? item.rating : "N/A"}
                </p>
              </div>
              {item.unavailable && <span className="text-sm italic text-red-400">Out of Stock</span>}
            </div>

            {item.unavailable && (
              <div className="mt-4 grid grid-cols-2 gap-3">
                {round.replacements[item.id].map(option => (
                  <button
                    key={option.id}
                    onClick={() => handleSelect(item.id, option.id)}
                    className={`p-2 rounded text-left border ${
                      selected[item.id] === option.id
                        ? "bg-green-600 border-green-400"
                        : "bg-gray-700 border-gray-500"
                    }`}
                  >
                    <p className="font-medium">{option.title}</p>
                    <p className="text-xs text-gray-300">
                      {option.price != null ? `$${option.price.toFixed(2)}` : "Price N/A"} | 
                      Rating: {option.rating != null ? option.rating : "N/A"}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
      {!submitted ? (
          <div className="mt-8 text-center">
            <button
              onClick={handleSubmit}
              className="bg-blue-600 text-white py-2 px-6 rounded hover:bg-blue-700"
            >
              Submit Replacements
            </button>
          </div>
        ) : (
          <div className="mt-10 text-center">
            <h3 className="text-2xl font-bold mb-2">Your Score: {score}/100</h3>
            <p className="text-sm text-gray-300 mb-4">
              Based on how close your replacements were in price and rating.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-green-600 text-white py-2 px-6 rounded hover:bg-green-700"
            >
              Play Again
            </button>
          </div>
      )}
    </div>
  );
}
