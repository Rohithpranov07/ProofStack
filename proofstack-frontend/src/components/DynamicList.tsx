"use client";

import { motion, AnimatePresence } from "framer-motion";

interface DynamicListProps<T> {
  items: T[];
  label: string;
  onAdd: () => void;
  onRemove: (index: number) => void;
  renderItem: (item: T, index: number) => React.ReactNode;
  error?: string;
}

export default function DynamicList<T>({
  items,
  label,
  onAdd,
  onRemove,
  renderItem,
  error,
}: DynamicListProps<T>) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-text-muted">{label}</span>
        <button
          type="button"
          onClick={onAdd}
          className="rounded-lg border border-border-subtle px-3 py-1.5 text-xs font-medium text-accent-primary transition-colors hover:bg-accent-primary/10"
        >
          + Add
        </button>
      </div>

      <AnimatePresence initial={false}>
        {items.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1">{renderItem(item, index)}</div>
              {items.length > 1 && (
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  className="mt-1 rounded-lg border border-border-subtle px-2.5 py-2 text-xs text-accent-red transition-colors hover:bg-accent-red/10"
                >
                  Remove
                </button>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {error && <p className="text-sm text-accent-red">{error}</p>}
    </div>
  );
}
