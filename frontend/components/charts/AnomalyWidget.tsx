"use client";

import { useEnergyStore } from "@/lib/store";
import { AlertOctagon } from "lucide-react";

export function AnomalyWidget() {
  const { latestReading } = useEnergyStore();
  const score = latestReading?.anomaly_score ?? 0;
  const isAnomalous = score > 0.5;
  const pct = Math.min(score * 100, 100);

  return (
    <div className={`bg-white rounded-xl shadow-sm border p-5 ${isAnomalous ? "border-danger/40" : "border-gray-100"}`}>
      <div className="flex items-center gap-2 mb-4">
        <AlertOctagon className={isAnomalous ? "text-danger" : "text-gray-400"} size={20} />
        <h2 className="text-base font-semibold text-gray-700">Anomaly Score</h2>
        {isAnomalous && (
          <span className="ml-auto text-xs font-semibold px-2 py-0.5 bg-danger/10 text-danger rounded-full">
            ANOMALY DETECTED
          </span>
        )}
      </div>
      <div className="flex items-end gap-4">
        <span className={`text-4xl font-bold ${isAnomalous ? "text-danger" : "text-gray-900"}`}>
          {score.toFixed(3)}
        </span>
        <span className="text-gray-400 text-sm mb-1">/ 1.0</span>
      </div>
      <div className="mt-3 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            backgroundColor: score < 0.3 ? "#22c55e" : score < 0.5 ? "#f59e0b" : "#ef4444",
          }}
        />
      </div>
      <p className="text-xs text-gray-400 mt-1">Threshold: 0.5 — LSTM-Autoencoder reconstruction error</p>
    </div>
  );
}
