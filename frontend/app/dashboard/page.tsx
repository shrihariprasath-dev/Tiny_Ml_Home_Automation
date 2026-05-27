import { Suspense } from "react";
import { PowerGauge } from "@/components/charts/PowerGauge";
import { EnergyChart } from "@/components/charts/EnergyChart";
import { AnomalyWidget } from "@/components/charts/AnomalyWidget";
import { OccupancyCard } from "@/components/charts/OccupancyCard";
import { StatCard } from "@/components/ui/StatCard";
import { Zap, Thermometer, Activity, AlertTriangle } from "lucide-react";

export default function OverviewPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Overview</h1>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Zap}        label="Live Power"       value="—"    unit="W"    color="blue" />
        <StatCard icon={Activity}   label="Today's Energy"   value="—"    unit="kWh"  color="green" />
        <StatCard icon={Thermometer} label="Temperature"     value="—"    unit="°C"   color="orange" />
        <StatCard icon={AlertTriangle} label="Anomalies (7d)" value="—"   unit=""     color="red" />
      </div>

      {/* Power gauge + live chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Suspense fallback={<div className="h-64 bg-white rounded-xl animate-pulse" />}>
            <PowerGauge />
          </Suspense>
        </div>
        <div className="lg:col-span-2">
          <Suspense fallback={<div className="h-64 bg-white rounded-xl animate-pulse" />}>
            <EnergyChart />
          </Suspense>
        </div>
      </div>

      {/* Anomaly + Occupancy row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Suspense fallback={<div className="h-48 bg-white rounded-xl animate-pulse" />}>
          <AnomalyWidget />
        </Suspense>
        <Suspense fallback={<div className="h-48 bg-white rounded-xl animate-pulse" />}>
          <OccupancyCard />
        </Suspense>
      </div>
    </div>
  );
}
