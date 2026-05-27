"use client";

import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { useEnergyStore } from "@/lib/store";

const MAX_WATTS = 3000;

export function PowerGauge() {
  const { latestReading } = useEnergyStore();
  const power = latestReading?.power_w ?? 0;
  const pct   = Math.min(power / MAX_WATTS, 1);

  const filled = pct * 180;
  const empty  = 180 - filled;

  const color = pct < 0.5 ? "#22c55e" : pct < 0.8 ? "#f59e0b" : "#ef4444";

  const data = [
    { value: filled, fill: color },
    { value: empty,  fill: "#f1f5f9" },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <h2 className="text-base font-semibold text-gray-700 mb-2">Live Power</h2>
      <div className="relative">
        <ResponsiveContainer width="100%" height={160}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="100%"
              startAngle={180}
              endAngle={0}
              innerRadius={70}
              outerRadius={100}
              paddingAngle={0}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-4">
          <span className="text-3xl font-bold text-gray-900">{power.toFixed(0)}</span>
          <span className="text-sm text-gray-500">Watts</span>
        </div>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500">
        <div>Voltage: <span className="font-medium text-gray-700">{latestReading?.voltage?.toFixed(1) ?? "—"} V</span></div>
        <div>Current: <span className="font-medium text-gray-700">{latestReading?.current?.toFixed(2) ?? "—"} A</span></div>
        <div>PF: <span className="font-medium text-gray-700">{latestReading?.power_factor?.toFixed(2) ?? "—"}</span></div>
        <div>kWh: <span className="font-medium text-gray-700">{latestReading?.energy_kwh?.toFixed(3) ?? "—"}</span></div>
      </div>
    </div>
  );
}
