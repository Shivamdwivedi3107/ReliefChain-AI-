import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from '../layouts/DashboardLayout';
import { CitizenDashboard } from '../pages/CitizenDashboard';
import { VolunteerDashboard } from '../pages/VolunteerDashboard';
import { AdminCommandCenter } from '../pages/AdminCommandCenter';
import { AICopilotPage } from '../pages/AICopilotPage';
import { DigitalTwinPage } from '../pages/DigitalTwinPage';
import { ShortageRadarPage } from '../pages/ShortageRadarPage';
import { TransparencyPage } from '../pages/TransparencyPage';
import { DisasterMapPage } from '../pages/DisasterMapPage';
import { LoginPage } from '../pages/LoginPage';
import { useAuth } from '../context/AuthContext';

export const AppRoutes: React.FC = () => {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<DashboardLayout />}>
        <Route index element={
          user?.role === 'citizen' ? <Navigate to="/citizen" replace /> :
          user?.role === 'volunteer' ? <Navigate to="/volunteer" replace /> :
          <Navigate to="/command-center" replace />
        } />
        <Route path="overview" element={<AdminCommandCenter />} />
        <Route path="citizen" element={<CitizenDashboard />} />
        <Route path="volunteer" element={<VolunteerDashboard />} />
        <Route path="command-center" element={<AdminCommandCenter />} />
        <Route path="copilot" element={<AICopilotPage />} />
        <Route path="digital-twin" element={<DigitalTwinPage />} />
        <Route path="shortage-radar" element={<ShortageRadarPage />} />
        <Route path="transparency" element={<TransparencyPage />} />
        <Route path="map" element={<DisasterMapPage />} />
        <Route path="system-health" element={<AdminCommandCenter />} />
        <Route path="pitch-deck" element={<TransparencyPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
