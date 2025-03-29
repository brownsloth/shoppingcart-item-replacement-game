import { Button } from "@/components/ui/button";
import Game from "@/components/Game";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col justify-between">
      <main className="px-6 py-12 flex-grow">
        <h1 className="text-4xl font-bold text-center mb-10">🛒 Item Replacement Game</h1>
        <Game />
      </main>

      <footer className="text-center py-6 border-t border-gray-800">
        <Link href="/retrain-dashboard" className="text-blue-400 hover:underline">
          View Retrain Dashboard
        </Link>
      </footer>
    </div>
  );
}
