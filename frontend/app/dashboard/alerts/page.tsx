"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { AlertTriangle, CheckCircle, BellOff, Filter } from "lucide-react";
import { format } from "date-fns";

interface Alert {
  id: string;
  device_id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  message: string;
  created_at: string;
  acknowledged_at: string | null;
}

const SEVERITY_COLORS: Record<string, string> = {
  low:      "bg-blue-50 text-blue-600 border-blue-100",
  medium:   "bg-warning/10 text-warning border-warning/20",
  high:     "bg-orange-50 text-orange-500 border-orange-100",
  critical: "bg-danger/10 text-danger border-danger/20",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<"all" | "unread">("unread");
  const [loading, setLoading] = useState(true);

  const fetchAlerts = () => {
    const acked = filter === "unread" ? "false" : "";
    apiClient.get<Alert[]>(`/api/alerts${acked ? "?acknowledged=false" : ""}`)
      .then(setAlerts)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchAlerts(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  const acknowledge = async (id: string) => {
    await apiClient.put(`/api/alerts/${id}/acknowledge`, {});
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, acknowledged_at: new Date().toISOString() } : a));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          {(["unread", "all"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
                filter === f ? "bg-brand-600 text-white" : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="text-gray-400 text-sm">Loading alerts…</div>}

      {!loading && alerts.length === 0 && (
        <div className="bg-white rounded-xl p-12 text-center text-gray-400 border border-dashed border-gray-200">
          <BellOff size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No alerts</p>
          <p className="text-sm mt-1">All clear! No unacknowledged alerts.</p>
        </div>
      )}

      <div className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`bg-white rounded-xl border p-4 flex items-start gap-4 ${
              alert.acknowledged_at ? "opacity-60" : ""
            }`}
          >
            <div className={`p-2 rounded-lg border ${SEVERITY_COLORS[alert.severity]}`}>
              <AlertTriangle size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${SEVERITY_COLORS[alert.severity]}`}>
                  {alert.severity.toUpperCase()}
                </span>
                <span className="text-xs text-gray-400 font-mono">{alert.device_id}</span>
                <span className="text-xs text-gray-400">{alert.type}</span>
              </div>
              <p className="text-sm text-gray-800 mt-1">{alert.message}</p>
              <p className="text-xs text-gray-400 mt-1">
                {format(new Date(alert.created_at), "MMM d, yyyy HH:mm:ss")}
              </p>
            </div>
            {!alert.acknowledged_at && (
              <button
                onClick={() => acknowledge(alert.id)}
                className="flex items-center gap-1 text-xs text-success hover:text-success/80 font-medium shrink-0"
              >
                <CheckCircle size={14} /> Acknowledge
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
