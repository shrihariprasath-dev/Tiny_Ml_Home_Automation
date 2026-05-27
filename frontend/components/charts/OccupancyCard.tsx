"use client";

import { useEnergyStore } from "@/lib/store";
import { Users } from "lucide-react";

export function OccupancyCard() {
  const { latestReading } = useEnergyStore();
  const prob     = latestReading?.occupancy_prob ?? null;
  const occupied = (prob ?? 0) >= 0.6;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-4">
        <Users className={occupied ? "text-success" : "text-gray-400"} size={20} />
        <h2 className="text-base font-semibold text-gray-700">Occupancy</h2>
      </div>
      <div className="flex items-center gap-4">
        <div
          className={`w-16 h-16 rounded-full flex items-center justify-center text-lg font-bold ${
            occupied ? "bg-success/10 text-success" : "bg-gray-100 text-gray-400"
          }`}
        >
          {occupied ? "IN" : "OUT"}
        </div>
        <div>
          <p className="text-3xl font-bold text-gray-900">
            {prob !== null ? `${(prob * 100).toFixed(0)}%` : "—"}
          </p>
          <p className="text-sm text-gray-500">probability occupied</p>
          <p className="text-xs text-gray-400 mt-0.5">Threshold: 60%</p>
        </div>
      </div>
    </div>
  );
}
