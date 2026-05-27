import { create } from "zustand";

export interface TelemetryReading {
  device_id:      string;
  ts:             number;
  voltage:        number;
  current:        number;
  power_w:        number;
  power_factor:   number;
  energy_kwh:     number;
  temperature:    number;
  humidity:       number;
  motion:         boolean;
  relay_states:   boolean[];
  anomaly_score:  number;
  occupancy_prob: number;
  firmware_version: string;
  time?: string;
}

interface EnergyState {
  latestReading: TelemetryReading | null;
  history:       TelemetryReading[];
  unreadAlerts:  number;
  setLatest:     (r: TelemetryReading) => void;
  pushHistory:   (r: TelemetryReading) => void;
  setUnreadAlerts: (n: number) => void;
}

const MAX_HISTORY = 288; // 24h at 5-min resolution

export const useEnergyStore = create<EnergyState>((set) => ({
  latestReading:  null,
  history:        [],
  unreadAlerts:   0,
  setLatest:      (r) => set({ latestReading: r }),
  pushHistory:    (r) =>
    set((s) => ({
      history: [
        ...s.history.slice(-(MAX_HISTORY - 1)),
        {
          ...r,
          time: new Date(r.ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    })),
  setUnreadAlerts: (n) => set({ unreadAlerts: n }),
}));
