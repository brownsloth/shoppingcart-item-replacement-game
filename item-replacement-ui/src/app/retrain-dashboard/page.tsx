"use client";

import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from "recharts";

type RetrainLog = {
  timestamp: string;
  mse: number;
  r2: number;
  num_samples: number;
};

export default function RetrainDashboard() {
  const [logs, setLogs] = useState<RetrainLog[]>([]);

  useEffect(() => {
    fetch("http://localhost:8000/retrain_logs")
      .then(res => res.json())
      .then(data => setLogs(data.logs || []))
      .catch(err => console.error("Failed to fetch retrain logs", err));
  }, []);

  if (logs.length === 0) return <div className="text-white text-center mt-8">No retrain logs yet</div>;

  return (
    <div className="p-8 text-white">
      <h1 className="text-3xl font-bold mb-6">Retrain History</h1>

      <div className="mb-10">
        <h2 className="text-xl font-semibold mb-2">📈 R² Over Time</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={logs}>
            <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 1]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="r2" stroke="#4ade80" name="R² Score" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mb-10">
        <h2 className="text-xl font-semibold mb-2">📉 MSE Over Time</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={logs}>
            <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="mse" stroke="#f87171" name="MSE" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">📦 Recent Runs</h2>
        <table className="w-full border border-gray-700 text-sm">
          <thead className="bg-gray-800 text-gray-300">
            <tr>
              <th className="p-2 text-left">Time</th>
              <th className="p-2 text-left">Samples</th>
              <th className="p-2 text-left">MSE</th>
              <th className="p-2 text-left">R²</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, i) => (
              <tr key={i} className="border-t border-gray-700">
                <td className="p-2">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="p-2">{log.num_samples}</td>
                <td className="p-2">{log.mse.toFixed(2)}</td>
                <td className="p-2">{log.r2.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
