import { useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { CheckCircle2, AlertCircle, X, Info } from "lucide-react";

type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
  action?: {
    label: string;
    onClick: () => void;
  };
}

let toastId = 0;
const listeners: Set<(toast: Toast) => void> = new Set();

export function toast(
  message: string,
  variant: ToastVariant = "info",
  action?: Toast["action"],
) {
  const t: Toast = { id: ++toastId, message, variant, action };
  listeners.forEach((fn) => fn(t));
}

const icons: Record<ToastVariant, typeof Info> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

const styles: Record<ToastVariant, string> = {
  success: "border-safe/30 bg-safe/10 text-safe",
  error: "border-danger/30 bg-danger/10 text-danger",
  info: "border-white/10 bg-white/10 text-zinc-100",
};

export function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((t: Toast) => {
    setToasts((prev) => [...prev, t]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== t.id));
    }, 4000);
  }, []);

  useEffect(() => {
    listeners.add(addToast);
    return () => { listeners.delete(addToast); };
  }, [addToast]);

  function dismiss(id: number) {
    setToasts((prev) => prev.filter((x) => x.id !== id));
  }

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
      {toasts.map((t) => {
        const Icon = icons[t.variant];
        return (
          <div
            key={t.id}
            className={cn(
              "slide-in-from-right flex items-center gap-2.5 rounded-2xl border px-4 py-3 text-sm shadow-[0_24px_48px_oklch(0.02_0.003_260_/_0.28)] backdrop-blur-xl",
              styles[t.variant],
            )}
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span className="flex-1">{t.message}</span>
            {t.action && (
              <button
                onClick={() => {
                  t.action?.onClick();
                  dismiss(t.id);
                }}
                className="rounded-full border border-white/10 px-2.5 py-1 text-xs font-medium text-zinc-100 transition-colors hover:bg-white/10"
              >
                {t.action.label}
              </button>
            )}
            <button onClick={() => dismiss(t.id)} className="opacity-60 hover:opacity-100">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
