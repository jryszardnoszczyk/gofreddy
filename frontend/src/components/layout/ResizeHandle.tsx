import { useCallback, useRef } from "react";
import { cn } from "@/lib/cn";

interface ResizeHandleProps {
  side: "left" | "right";
  onResize: (deltaX: number) => void;
  onResizeStart?: () => void;
  onResizeEnd?: () => void;
  onDoubleClick: () => void;
  ariaLabel?: string;
  className?: string;
}

export function ResizeHandle({
  side,
  onResize,
  onResizeStart,
  onResizeEnd,
  onDoubleClick,
  ariaLabel = "Resize panels",
  className,
}: ResizeHandleProps) {
  const startX = useRef(0);
  const dragging = useRef(false);

  const onPointerDown = useCallback(
    (e: React.PointerEvent) => {
      e.preventDefault();
      startX.current = e.clientX;
      dragging.current = true;
      onResizeStart?.();
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";

      const onPointerMove = (ev: PointerEvent) => {
        const delta = ev.clientX - startX.current;
        startX.current = ev.clientX;
        // For a handle on the left edge, dragging left means the panel should grow (negative delta = positive resize)
        onResize(side === "right" ? delta : -delta);
      };

      const onPointerUp = () => {
        dragging.current = false;
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        document.removeEventListener("pointermove", onPointerMove);
        document.removeEventListener("pointerup", onPointerUp);
        onResizeEnd?.();
      };

      document.addEventListener("pointermove", onPointerMove);
      document.addEventListener("pointerup", onPointerUp);
    },
    [onResize, onResizeEnd, onResizeStart, side],
  );

  return (
    <div
      onPointerDown={onPointerDown}
      onDoubleClick={onDoubleClick}
      role="separator"
      aria-orientation="vertical"
      aria-label={ariaLabel}
      className={cn(
        "group/handle absolute top-0 z-10 flex h-full w-[6px] cursor-col-resize items-center justify-center",
        side === "right" ? "right-0 translate-x-1/2" : "left-0 -translate-x-1/2",
        className,
      )}
    >
      <div className="h-8 w-[3px] rounded-full bg-zinc-700 opacity-0 transition-opacity group-hover/handle:opacity-100" />
    </div>
  );
}
