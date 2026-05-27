"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { RelayToggle } from "@/components/controls/RelayToggle";
import { ScheduleEditor } from "@/components/controls/ScheduleEditor";
import { Cpu, Plus } from "lucide-react";

interface Device {
  id: string;
  device_id: string;
  name: string;
  room: string;
  relay_states: boolean[];
  firmware_ver: string;
  online: boolean;
}

export default function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [selected, setSelected] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.get<Device[]>("/api/devices")
      .then((d) => setDevices(d))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleRelayToggle = async (deviceId: string, relay: number, state: boolean) => {
    await apiClient.put(`/api/devices/${deviceId}/relay`, { relay, state });
    setDevices((prev) =>
      prev.map((d) => {
        if (d.device_id !== deviceId) return d;
        const relays = [...d.relay_states];
        relays[relay] = state;
        return { ...d, relay_states: relays };
      })
    );
  };

  const RELAY_LABELS = ["Lights", "Fan", "AC", "Spare"];

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-400">Loading devices…</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Devices</h1>
        <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors">
          <Plus size={16} /> Add Device
        </button>
      </div>

      {devices.length === 0 && (
        <div className="bg-white rounded-xl p-12 text-center text-gray-400 border border-dashed border-gray-200">
          <Cpu size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-medium">No devices registered yet</p>
          <p className="text-sm mt-1">Add your first ESP32 device to get started.</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {devices.map((device) => (
          <div
            key={device.id}
            className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-900">{device.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{device.device_id} · {device.room}</p>
              </div>
              <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                device.online
                  ? "bg-success/10 text-success"
                  : "bg-gray-100 text-gray-400"
              }`}>
                {device.online ? "Online" : "Offline"}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
              {(device.relay_states ?? [false, false, false, false]).map((state, i) => (
                <RelayToggle
                  key={i}
                  label={RELAY_LABELS[i]}
                  checked={state}
                  disabled={!device.online}
                  onChange={(v) => handleRelayToggle(device.device_id, i, v)}
                />
              ))}
            </div>

            <button
              onClick={() => setSelected(device)}
              className="text-xs text-brand-600 hover:underline"
            >
              Manage schedules →
            </button>
          </div>
        ))}
      </div>

      {selected && (
        <ScheduleEditor device={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
