import { cn } from "@/lib/cn";

export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={cn("text-white", className)}
    >
      <rect x="4" y="4" width="9" height="9" rx="3" fill="currentColor" opacity="0.22" />
      <rect x="10.5" y="10.5" width="9.5" height="9.5" rx="3" stroke="currentColor" strokeWidth="1.6" />
      <path d="M8 8h4.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M8 11h6.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M12 16h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
