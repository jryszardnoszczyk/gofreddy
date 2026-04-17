import { cn } from "@/lib/cn";

export function Card({
  children,
  className,
  hover = false,
  interactive = false,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { hover?: boolean; interactive?: boolean }) {
  return (
    <div
      className={cn(
        "app-panel-surface rounded-[16px] p-5 transition-all duration-200",
        hover && "cursor-pointer hover:bg-surface-raised/90 hover:shadow-[0_8px_18px_oklch(0.08_0.003_255_/_0.08)]",
        interactive && "focus-within:border-white/12 focus-within:ring-2 focus-within:ring-white/8",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-center justify-between gap-3", className)}>
      {children}
    </div>
  );
}

export function CardTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3 className={cn("text-sm font-semibold tracking-tight text-zinc-100", className)}>
      {children}
    </h3>
  );
}
