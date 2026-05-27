import { LucideIcon } from "lucide-react";

interface Props {
  icon:  LucideIcon;
  label: string;
  value: string | number;
  unit:  string;
  color: "blue" | "green" | "orange" | "red";
}

const COLORS = {
  blue:   { bg: "bg-blue-50",   icon: "text-blue-500"  },
  green:  { bg: "bg-green-50",  icon: "text-green-500" },
  orange: { bg: "bg-orange-50", icon: "text-orange-500" },
  red:    { bg: "bg-red-50",    icon: "text-red-500"   },
};

export function StatCard({ icon: Icon, label, value, unit, color }: Props) {
  const c = COLORS[color];
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${c.bg}`}>
          <Icon className={c.icon} size={20} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">
            {value} <span className="text-sm font-normal text-gray-400">{unit}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
