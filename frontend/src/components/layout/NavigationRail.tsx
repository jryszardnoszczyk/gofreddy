import { NavLink } from "react-router-dom";
import { cn } from "@/lib/cn";
import { ROUTES } from "@/lib/routes";
import { BrandPopoverButton } from "@/components/brand/BrandPopoverButton";
import { Briefcase, Settings } from "lucide-react";

export function NavigationRail() {
  return (
    <div className="hidden md:flex shrink-0 w-12 flex-col items-center gap-1 border-r border-white/6 bg-surface-base py-3">
      <div className="mb-3">
        <BrandPopoverButton />
      </div>

      <NavLink
        to={ROUTES.dashboardSessions}
        className={({ isActive }) =>
          cn(
            "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
            isActive
              ? "bg-white/8 text-zinc-100"
              : "text-zinc-500 hover:bg-surface-raised hover:text-zinc-300",
          )
        }
        title="Sessions"
        aria-label="Sessions"
      >
        <Briefcase className="h-[18px] w-[18px]" />
      </NavLink>

      <div className="flex-1" />

      <NavLink
        to={ROUTES.dashboardSettings}
        className={({ isActive }) =>
          cn(
            "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
            isActive
              ? "bg-white/8 text-zinc-100"
              : "text-zinc-500 hover:bg-surface-raised hover:text-zinc-300",
          )
        }
        title="Settings"
        aria-label="Settings"
      >
        <Settings className="h-[18px] w-[18px]" />
      </NavLink>
    </div>
  );
}
