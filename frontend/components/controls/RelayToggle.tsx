"use client";

interface Props {
  label:    string;
  checked:  boolean;
  disabled?: boolean;
  onChange: (value: boolean) => void;
}

export function RelayToggle({ label, checked, disabled, onChange }: Props) {
  return (
    <div className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-colors ${
      checked ? "bg-brand-50 border-brand-200" : "bg-gray-50 border-gray-200"
    }`}>
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <button
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 disabled:opacity-40 disabled:cursor-not-allowed ${
          checked ? "bg-brand-600" : "bg-gray-300"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  );
}
