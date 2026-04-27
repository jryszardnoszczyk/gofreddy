import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation, useParams } from "react-router-dom";
import { AuthProvider, useAuth } from "@/components/AuthProvider";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { AuthCallbackPage } from "@/pages/AuthCallbackPage";
import { LoginPage } from "@/pages/LoginPage";
import { SessionsPage } from "@/pages/SessionsPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { ROUTES } from "@/lib/routes";
import "./index.css";

function ProtectedRoute() {
  const { session, loading } = useAuth();
  const location = useLocation();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }
  if (!session) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    const target =
      next && next !== "/"
        ? `${ROUTES.login}?next=${encodeURIComponent(next)}`
        : ROUTES.login;
    return <Navigate to={target} replace />;
  }
  return <Outlet />;
}

function RootRedirect() {
  const { session, loading } = useAuth();
  if (loading) return null;
  return <Navigate to={session ? ROUTES.dashboardSessions : ROUTES.login} replace />;
}

function PortalRedirect() {
  const { slug } = useParams();
  const target = slug
    ? `${ROUTES.dashboardSessions}?client=${encodeURIComponent(slug)}`
    : ROUTES.dashboardSessions;
  return <Navigate to={target} replace />;
}

createRoot(document.getElementById("app")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<RootRedirect />} />
          <Route path={ROUTES.login} element={<LoginPage />} />
          <Route path={ROUTES.authCallback} element={<AuthCallbackPage />} />
          <Route path="/portal/:slug" element={<PortalRedirect />} />

          <Route element={<ProtectedRoute />}>
            <Route
              path={ROUTES.dashboard}
              element={
                <ErrorBoundary label="App">
                  <DashboardLayout />
                </ErrorBoundary>
              }
            >
              <Route index element={<Navigate to={ROUTES.dashboardSessions} replace />} />
              <Route path={ROUTES.dashboardSessionsChild} element={<SessionsPage />} />
              <Route path={ROUTES.dashboardSettingsChild} element={<SettingsPage />} />
            </Route>

            <Route path="*" element={<Navigate to={ROUTES.dashboardSessions} replace />} />
          </Route>

          <Route path="*" element={<Navigate to={ROUTES.login} replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
