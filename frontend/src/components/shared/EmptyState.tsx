import { cn } from "@/lib/cn";

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "app-empty-stage rounded-[20px] border border-white/5 py-24 text-center",
        "flex flex-col items-center justify-center px-6",
        className,
      )}
    >
      <div className="mb-5">
        <div className="app-mark-shell flex h-16 w-16 items-center justify-center rounded-[16px] text-zinc-200">
          {icon}
        </div>
      </div>
      <h3 className="mb-1.5 text-base font-semibold text-zinc-100">{title}</h3>
      <p className="mb-6 max-w-sm text-[13px] leading-relaxed text-zinc-400">{description}</p>
      {action}
    </div>
  );
}
