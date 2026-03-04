import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@/auth/AuthProvider";
import { ProtectedRoute } from "@/auth/ProtectedRoute";
import { LoginPage } from "@/auth/LoginPage";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { TeamOverviewPage } from "@/features/team/TeamOverviewPage";
import { AthleteDetailPage } from "@/features/athlete/AthleteDetailPage";
import { SessionListPage } from "@/features/sessions/SessionListPage";
import { SessionCreateForm } from "@/features/sessions/SessionCreateForm";
import { AnomalyFeed } from "@/features/anomalies/AnomalyFeed";
import { WellnessOverviewPage } from "@/features/wellness/WellnessOverviewPage";
import { AthleteWellnessDetail } from "@/features/wellness/AthleteWellnessDetail";
import { MyVitalsPage } from "@/features/vitals/MyVitalsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route index element={<TeamOverviewPage />} />
                <Route path="team" element={<Navigate to="/" replace />} />
                <Route path="athletes/:id" element={<AthleteDetailPage />} />
                <Route path="sessions" element={<SessionListPage />} />
                <Route path="sessions/new" element={<SessionCreateForm />} />
                <Route path="wellness" element={<WellnessOverviewPage />} />
                <Route path="wellness/:athleteId" element={<AthleteWellnessDetail />} />
                <Route path="my-vitals" element={<MyVitalsPage />} />
                <Route path="anomalies" element={<AnomalyFeed />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
