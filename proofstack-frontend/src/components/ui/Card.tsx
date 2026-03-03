import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-border-subtle bg-bg-card p-8 shadow-md shadow-black/10 ${className}`}
    >
      {children}
    </div>
  );
}
