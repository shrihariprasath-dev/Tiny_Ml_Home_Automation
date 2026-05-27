"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, BarChart2, Cpu, Brain,
  Bell, Settings, Zap,
} from "lucide-react";
import { clsx } from "clsx";

const NAV = [
  { href: "/dashboard",           label: "Overview",         icon: LayoutDashboard },
  { href: "/dashboard/analytics", label: "Analytics",        icon: BarChart2 },
  { href: "/dashboard/devices",   label: "Devices",          icon: Cpu },
  { href: "/dashboard/ai",        label: "AI Predictions",   icon: Brain },
  { href: "/dashboard/alerts",    label: "Alerts",           icon: Bell },
  { href: "/dashboard/settings",  label: "Settings",         icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-brand-900 flex flex-col shrink-0">
      {/* Logo */}
      <div className="h-14 flex items-center gap-2.5 px-4 border-b border-brand-700/50">
        <div className="p-1.5 bg-brand-500 rounded-lg">
          <Zap className="text-white" size={16} />
        </div>
        <span className="text-white font-semibold text-sm leading-tight">
          Smart Home<br />
          <span className="text-brand-300 font-normal text-xs">Power Manager</span>
        </span>
      </div>

      {/* Nav links */}
      <nav className="flex-1 py-4 space-y-0.5 px-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/dashboard" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-brand-600 text-white"
                  : "text-brand-200 hover:bg-brand-700/50 hover:text-white"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 text-xs text-brand-400">v1.0.0</div>
    </aside>
  );
}
