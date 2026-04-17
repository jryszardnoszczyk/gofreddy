import { cn } from "@/lib/cn";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

const variantStyles: Record<Variant, string> = {
  primary:
    "border border-white/10 bg-zinc-100 text-zinc-950 shadow-[0_1px_2px_rgba(0,0,0,0.18)] hover:bg-white active:bg-zinc-200",
  secondary:
    "border border-white/6 bg-surface-raised text-zinc-100 hover:bg-surface-overlay",
  ghost: "text-zinc-400 hover:text-zinc-100 hover:bg-white/5",
  danger: "bg-danger/15 text-danger hover:bg-danger/25 border border-danger/25",
};

const sizeStyles: Record<Size, string> = {
  sm: "h-8 px-3 text-xs gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-6 text-sm gap-2",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "md", loading, children, className, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center rounded-[12px] font-medium transition-all duration-150",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/20 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-base",
          "disabled:opacity-40 disabled:pointer-events-none disabled:saturate-50",
          variantStyles[variant],
          sizeStyles[size],
          className,
        )}
        {...props}
      >
        {loading && (
          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  },
);

Button.displayName = "Button";
