"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useSession } from "next-auth/react";
import { Save, User, Bell, Shield } from "lucide-react";

const profileSchema = z.object({
  email:    z.string().email(),
  name:     z.string().min(2),
});
type ProfileForm = z.infer<typeof profileSchema>;

const thresholdSchema = z.object({
  power_threshold_w:   z.coerce.number().min(0),
  anomaly_threshold:   z.coerce.number().min(0).max(1),
  alert_email:         z.string().email(),
});
type ThresholdForm = z.infer<typeof thresholdSchema>;

export default function SettingsPage() {
  const { data: session } = useSession();
  const [tab, setTab] = useState<"profile" | "thresholds" | "security">("profile");
  const [saved, setSaved] = useState(false);

  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { email: session?.user?.email ?? "", name: session?.user?.name ?? "" },
  });

  const thresholdForm = useForm<ThresholdForm>({
    resolver: zodResolver(thresholdSchema),
    defaultValues: { power_threshold_w: 2000, anomaly_threshold: 0.5, alert_email: session?.user?.email ?? "" },
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const TABS = [
    { id: "profile",    label: "Profile",    icon: User },
    { id: "thresholds", label: "Thresholds", icon: Bell },
    { id: "security",   label: "Security",   icon: Shield },
  ] as const;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Settings</h1>

      <div className="flex gap-2 border-b border-gray-200">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === id
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={15} />{label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 max-w-lg">
        {tab === "profile" && (
          <form onSubmit={profileForm.handleSubmit(handleSave)} className="space-y-4">
            <h2 className="font-semibold text-gray-700">Profile Information</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input {...profileForm.register("name")} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input {...profileForm.register("email")} type="email" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <SaveButton saved={saved} />
          </form>
        )}

        {tab === "thresholds" && (
          <form onSubmit={thresholdForm.handleSubmit(handleSave)} className="space-y-4">
            <h2 className="font-semibold text-gray-700">Alert Thresholds</h2>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Power Threshold (W)</label>
              <input {...thresholdForm.register("power_threshold_w")} type="number" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
              <p className="text-xs text-gray-400 mt-1">Alert when power exceeds this value</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Anomaly Score Threshold (0–1)</label>
              <input {...thresholdForm.register("anomaly_threshold")} type="number" step="0.01" min="0" max="1" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Alert Email</label>
              <input {...thresholdForm.register("alert_email")} type="email" className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 outline-none" />
            </div>
            <SaveButton saved={saved} />
          </form>
        )}

        {tab === "security" && (
          <div className="space-y-4">
            <h2 className="font-semibold text-gray-700">Security</h2>
            <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 text-sm text-gray-600 space-y-2">
              <p>• JWT access tokens expire after <strong>15 minutes</strong></p>
              <p>• Refresh tokens are valid for <strong>7 days</strong></p>
              <p>• Passwords are hashed with <strong>bcrypt</strong></p>
              <p>• All API traffic requires <strong>TLS 1.2+</strong></p>
            </div>
            <button className="px-4 py-2 text-sm font-medium text-danger border border-danger/30 rounded-lg hover:bg-danger/5 transition-colors">
              Change Password
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function SaveButton({ saved }: { saved: boolean }) {
  return (
    <button
      type="submit"
      className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors"
    >
      <Save size={14} />
      {saved ? "Saved!" : "Save Changes"}
    </button>
  );
}
