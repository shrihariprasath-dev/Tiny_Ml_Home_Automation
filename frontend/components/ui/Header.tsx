"use client";

import { signOut } from "next-auth/react";
import { Bell, LogOut } from "lucide-react";

interface Props {
  user?: { name?: string | null; email?: string | null } | null;
}

export function Header({ user }: Props) {
  return (
    <header className="h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 shrink-0">
      <div />
      <div className="flex items-center gap-3">
        <button className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500 relative">
          <Bell size={18} />
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-brand-600 flex items-center justify-center text-white text-xs font-bold">
            {user?.name?.[0]?.toUpperCase() ?? user?.email?.[0]?.toUpperCase() ?? "U"}
          </div>
          <span className="text-sm font-medium text-gray-700 hidden md:block">
            {user?.name ?? user?.email ?? "User"}
          </span>
        </div>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="p-1.5 hover:bg-gray-100 rounded-lg text-gray-500"
          title="Sign out"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}
