import { cn } from "@/lib/cn";
import { AlertCircle, AlertTriangle, Info } from "lucide-react";

type AlertVariant = "error" | "warning" | "info";

const variants: Record<AlertVariant, { style: string; Icon: typeof Info }> = {
  error: { style: "border-danger/20 bg-danger/5 text-danger", Icon: AlertCircle },
  warning: { style: "border-warning/20 bg-warning/5 text-warning", Icon: AlertTriangle },
  info: { style: "border-white/10 bg-white/6 text-zinc-200", Icon: Info },
};

export function AlertBanner({
  message,
  variant = "error",
  className,
  children,
}: {
  message: string;
  variant?: AlertVariant;
  className?: string;
  children?: React.ReactNode;
}) {
  const { style, Icon } = variants[variant];
  return (
    <div className={cn("flex items-center gap-2.5 rounded-2xl border px-4 py-3 text-sm shadow-[inset_0_1px_0_oklch(1_0_0_/_0.04)]", style, className)}>
      <Icon className="h-4 w-4 shrink-0" />
      <span className="flex-1">{message}</span>
      {children}
    </div>
  );
}
