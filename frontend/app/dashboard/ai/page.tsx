"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from "recharts";
import { apiClient } from "@/lib/api";
import { Brain, TrendingUp, AlertOctagon, Users } from "lucide-react";

interface AnomalyEvent {
  time: string;
  device_id: string;
  anomaly_score: number;
}

interface OccupancyResult {
  device_id: string;
  occupancy_prob: number | null;
  occupied: boolean;
}

interface ForecastResult {
  device_id: string;
  next_hour_kwh: number;
  confidence: string;
}

export default function AIPredictionsPage() {
  const [anomalies, setAnomalies] = useState<AnomalyEvent[]>([]);
  const [occupancy, setOccupancy] = useState<OccupancyResult[]>([]);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      apiClient.get<AnomalyEvent[]>("/api/ai/anomalies?limit=20"),
      apiClient.get<OccupancyResult[]>("/api/ai/occupancy"),
      apiClient.get<ForecastResult>("/api/ai/forecast?device_id=esp32_room_01"),
    ]).then(([a, o, f]) => {
      if (a.status === "fulfilled") setAnomalies(a.value);
      if (o.status === "fulfilled") setOccupancy(o.value);
      if (f.status === "fulfilled") setForecast(f.value);
      setLoading(false);
    });
  }, []);

  const anomalyChartData = anomalies.map((e) => ({
    time: new Date(e.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    score: e.anomaly_score,
  }));

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">Loading AI data…</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">AI Predictions</h1>

      {/* Cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Forecast */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="text-brand-500" size={20} />
            <h3 className="font-semibold text-gray-700">Next-Hour Forecast</h3>
          </div>
          {forecast ? (
            <div>
              <p className="text-3xl font-bold text-gray-900">
                {forecast.next_hour_kwh.toFixed(3)} <span className="text-lg font-normal text-gray-500">kWh</span>
              </p>
              <p className="text-xs text-gray-400 mt-1">Confidence: {forecast.confidence}</p>
            </div>
          ) : (
            <p className="text-gray-400 text-sm">Model not available</p>
          )}
        </div>

        {/* Anomaly count */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertOctagon className="text-danger" size={20} />
            <h3 className="font-semibold text-gray-700">Anomalies (last 7d)</h3>
          </div>
          <p className="text-3xl font-bold text-gray-900">{anomalies.length}</p>
          <p className="text-xs text-gray-400 mt-1">Events above threshold</p>
        </div>

        {/* Occupancy */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <div className="flex items-center gap-2 mb-3">
            <Users className="text-success" size={20} />
            <h3 className="font-semibold text-gray-700">Occupancy</h3>
          </div>
          {occupancy.length > 0 ? (
            <div className="space-y-2">
              {occupancy.slice(0, 3).map((o) => (
                <div key={o.device_id} className="flex justify-between items-center text-sm">
                  <span className="text-gray-600 truncate max-w-[120px]">{o.device_id}</span>
                  <span className={`font-semibold ${o.occupied ? "text-success" : "text-gray-400"}`}>
                    {o.occupied ? "Occupied" : "Empty"} {o.occupancy_prob !== null ? `(${(o.occupancy_prob * 100).toFixed(0)}%)` : ""}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm">No data</p>
          )}
        </div>
      </div>

      {/* Anomaly score chart */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-4">
          <Brain className="text-brand-500" size={20} />
          <h2 className="font-semibold text-gray-700">Anomaly Score Timeline</h2>
        </div>
        {anomalyChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={anomalyChartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="time" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: 8 }} formatter={(v: number) => [v.toFixed(4), "Score"]} />
              <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="4 4" label={{ value: "threshold", position: "right", fontSize: 10 }} />
              <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={false} name="Anomaly Score" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-400 text-sm text-center py-8">No anomaly events in the last 7 days.</p>
        )}
      </div>

      {/* Anomaly log table */}
      {anomalies.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
          <h2 className="font-semibold text-gray-700 mb-3">Anomaly Log</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-gray-100">
                  <th className="pb-2 pr-4">Time</th>
                  <th className="pb-2 pr-4">Device</th>
                  <th className="pb-2">Score</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.map((e, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 pr-4 text-gray-500">{new Date(e.time).toLocaleString()}</td>
                    <td className="py-2 pr-4 font-mono text-xs">{e.device_id}</td>
                    <td className="py-2">
                      <span className="px-2 py-0.5 bg-danger/10 text-danger rounded font-medium">
                        {e.anomaly_score.toFixed(4)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
