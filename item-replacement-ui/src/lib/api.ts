export async function fetchGameRound() {
  const res = await fetch("http://localhost:8000/generate_round");
  if (!res.ok) {
    throw new Error("Failed to fetch game round");
  }
  return res.json();
}
