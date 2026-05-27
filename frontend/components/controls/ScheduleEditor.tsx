"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { apiClient } from "@/lib/api";
import { X, Plus, Trash2 } from "lucide-react";

const scheduleSchema = z.object({
  cron_expr: z.string().min(9, "Enter a valid cron expression"),
  relay:     z.coerce.number().min(0).max(3),
  state:     z.boolean(),
  enabled:   z.boolean(),
});
type ScheduleForm = z.infer<typeof scheduleSchema>;

interface Props {
  device: { device_id: string; name: string };
  onClose: () => void;
}

export function ScheduleEditor({ device, onClose }: Props) {
  const [schedules, setSchedules] = useState<(ScheduleForm & { id: string })[]>([]);
  const [adding, setAdding] = useState(false);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ScheduleForm>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: { cron_expr: "0 22 * * *", relay: 0, state: false, enabled: true },
  });

  const onAdd = async (data: ScheduleForm) => {
    const created = await apiClient.post<{ id: string } & ScheduleForm>("/api/schedules", {
      ...data,
      device_id: device.device_id,
      action: { relay: data.relay, state: data.state },
    });
    setSchedules((prev) => [...prev, created]);
    reset();
    setAdding(false);
  };

  const onDelete = async (id: string) => {
    await apiClient.delete(`/api/schedules/${id}`);
    setSchedules((prev) => prev.filter((s) => s.id !== id));
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">Schedules — {device.name}</h2>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg"><X size={16} /></button>
        </div>

        {schedules.length === 0 && !adding && (
          <p className="text-sm text-gray-400 text-center py-4">No schedules yet.</p>
        )}

        <div className="space-y-2 mb-4">
          {schedules.map((s) => (
            <div key={s.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
              <div className="text-sm">
                <span className="font-mono text-gray-700">{s.cron_expr}</span>
                <span className="text-gray-400 ml-2">→ Relay {s.relay} {s.state ? "ON" : "OFF"}</span>
              </div>
              <button onClick={() => onDelete(s.id)} className="text-danger hover:text-danger/70">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>

        {adding ? (
          <form onSubmit={handleSubmit(onAdd)} className="space-y-3 border-t border-gray-100 pt-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Cron Expression</label>
              <input {...register("cron_expr")} placeholder="0 22 * * *" className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-brand-500 outline-none" />
              {errors.cron_expr && <p className="text-danger text-xs mt-1">{errors.cron_expr.message}</p>}
              <p className="text-xs text-gray-400 mt-1">Format: min hour dom month dow</p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Relay (0–3)</label>
                <input {...register("relay")} type="number" min={0} max={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Action</label>
                <select {...register("state", { setValueAs: (v) => v === "true" })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 outline-none">
                  <option value="true">Turn ON</option>
                  <option value="false">Turn OFF</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="flex-1 py-2 bg-brand-600 text-white text-sm rounded-lg font-medium hover:bg-brand-700 transition-colors">Add</button>
              <button type="button" onClick={() => setAdding(false)} className="px-4 py-2 border border-gray-200 text-sm rounded-lg hover:bg-gray-50 transition-colors">Cancel</button>
            </div>
          </form>
        ) : (
          <button
            onClick={() => setAdding(true)}
            className="w-full flex items-center justify-center gap-2 py-2 border border-dashed border-brand-300 text-brand-600 text-sm rounded-lg hover:bg-brand-50 transition-colors"
          >
            <Plus size={14} /> Add Schedule
          </button>
        )}
      </div>
    </div>
  );
}
