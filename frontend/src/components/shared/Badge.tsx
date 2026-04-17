import { cn } from "@/lib/cn";

type Variant = "safe" | "danger" | "warning" | "neutral" | "brand";

const variants: Record<Variant, string> = {
  safe: "bg-safe/15 text-safe border-safe/25",
  danger: "bg-danger/15 text-danger border-danger/25",
  warning: "bg-warning/15 text-warning border-warning/25",
  neutral: "border-white/8 bg-white/6 text-zinc-200",
  brand: "border-white/12 bg-white/10 text-zinc-100",
};

export function Badge({
  variant = "neutral",
  children,
  className,
}: {
  variant?: Variant;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium shadow-[inset_0_1px_0_oklch(1_0_0_/_0.05)]",
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}
