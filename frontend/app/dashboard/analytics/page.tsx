"use client";

import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line,
} from "recharts";
import { useEnergyStore } from "@/lib/store";

const PERIODS = ["hourly", "daily", "monthly"] as const;
type Period = typeof PERIODS[number];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("daily");
  const { history } = useEnergyStore();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Energy Analytics</h1>
        <div className="flex gap-2">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                period === p
                  ? "bg-brand-600 text-white"
                  : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
              }`}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Consumption bar chart */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Energy Consumption (kWh)</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={history} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ borderRadius: 8, border: "1px solid #e5e7eb" }}
              formatter={(v: number) => [`${v.toFixed(3)} kWh`, "Energy"]}
            />
            <Legend />
            <Bar dataKey="energy_kwh" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Energy (kWh)" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Power trend */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Power Trend (W)</h2>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={history} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip contentStyle={{ borderRadius: 8 }} />
            <Line
              type="monotone"
              dataKey="power_w"
              stroke="#22c55e"
              strokeWidth={2}
              dot={false}
              name="Power (W)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Per-room breakdown placeholder */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-base font-semibold text-gray-700 mb-3">Per-Room Breakdown</h2>
        <p className="text-sm text-gray-400">
          Room-level data populates once devices are assigned to rooms via Settings.
        </p>
      </div>
    </div>
  );
}
