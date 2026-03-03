"use client";

import { SelectHTMLAttributes } from "react";

interface SelectInputProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string;
  options: { value: string; label: string }[];
}

export default function SelectInput({
  label,
  error,
  id,
  options,
  ...props
}: SelectInputProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-text-secondary">
        {label}
      </label>
      <select
        id={id}
        className="rounded-lg border border-border-subtle bg-bg-primary px-4 py-2.5 text-sm text-text-primary outline-none transition-colors focus:border-accent-primary"
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-sm text-accent-red">{error}</p>}
    </div>
  );
}
