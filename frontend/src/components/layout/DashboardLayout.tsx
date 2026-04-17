import { Outlet } from "react-router-dom";
import { NavigationRail } from "./NavigationRail";

export function DashboardLayout() {
  return (
    <div className="flex h-screen bg-background">
      <NavigationRail />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
