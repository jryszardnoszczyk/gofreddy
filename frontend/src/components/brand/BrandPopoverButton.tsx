import { useEffect, useId, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { BrandMark } from "./BrandMark";

interface BrandPopoverButtonProps {
  buttonClassName?: string;
  iconClassName?: string;
  popoverClassName?: string;
}

export function BrandPopoverButton({
  buttonClassName,
  iconClassName,
  popoverClassName,
}: BrandPopoverButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const popoverId = useId();

  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: PointerEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label="Open Freddy workspace details"
        aria-expanded={isOpen}
        aria-controls={popoverId}
        onClick={() => setIsOpen((current) => !current)}
        className={cn(
          "flex h-9 w-9 items-center justify-center rounded-[12px] border border-white/6 bg-surface-raised text-zinc-100 transition-all duration-200 hover:border-white/12 hover:bg-white/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/14",
          buttonClassName,
        )}
      >
        <BrandMark className={cn("h-4 w-4", iconClassName)} />
      </button>

      {isOpen && (
        <div
          id={popoverId}
          role="dialog"
          aria-label="Freddy workspace details"
          className={cn(
            "absolute left-0 top-full z-30 mt-3 w-72 max-w-[calc(100vw-2rem)] overflow-hidden rounded-[24px] border border-white/10 bg-[#12151b]/95 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.45)] backdrop-blur-xl",
            popoverClassName,
          )}
        >
          <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.16),transparent_58%)]" />
          <div className="relative">
            <div className="flex items-start gap-3">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-[16px] border border-white/10 bg-white/[0.06] text-zinc-50">
                <BrandMark className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="font-display text-lg font-semibold tracking-tight text-zinc-50">
                  Freddy
                </p>
                <p className="mt-1 text-sm leading-relaxed text-zinc-300">
                  Video intelligence workspace for search, analysis, and studio-ready iteration.
                </p>
              </div>
            </div>

            <div className="mt-4 rounded-[18px] border border-white/8 bg-white/[0.03] px-3 py-3">
              <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">Workspace</p>
              <p className="mt-1 text-sm text-zinc-200">
                One canvas for chat, review, and video creation.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
