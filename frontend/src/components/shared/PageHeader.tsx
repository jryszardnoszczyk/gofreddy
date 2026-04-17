import { cn } from "@/lib/cn";

export function PageHeader({
  icon,
  title,
  description,
  actions,
  className,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("relative mb-8 flex items-start justify-between gap-4", className)}>
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[12px] border border-white/6 bg-surface text-zinc-200">
          {icon}
        </div>
        <div>
          <h1 className="text-[1.15rem] font-semibold tracking-tight text-zinc-100">{title}</h1>
          <p className="mt-1 max-w-2xl text-sm text-zinc-400">{description}</p>
        </div>
      </div>
      {actions}
    </div>
  );
}
