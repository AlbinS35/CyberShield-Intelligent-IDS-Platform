import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { SocketProvider } from './context/SocketContext'
import ProtectedRoute from './components/layout/ProtectedRoute'
import DashboardLayout from './components/layout/DashboardLayout'

// Auth Pages
import LoginPage          from './pages/auth/LoginPage'
import SignupPage         from './pages/auth/SignupPage'
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage'
import ResetPasswordPage  from './pages/auth/ResetPasswordPage'
import LandingPage        from './pages/LandingPage'

// Role-specific Dashboard Pages
import AnalystDashboard    from './pages/Analyst/AnalystDashboard'
import AlertFeed           from './pages/Analyst/AlertFeed'
import AlertDetail         from './pages/Analyst/AlertDetail'
import NetworkEvents       from './pages/Analyst/NetworkEvents'
import IncidentManager     from './pages/Analyst/IncidentManager'

import CaseManagement      from './pages/Investigator/CaseManagement'
import EvidenceVault       from './pages/Investigator/EvidenceVault'
import ForensicTimeline    from './pages/Investigator/ForensicTimeline'

import AssetRegistry       from './pages/Admin/AssetRegistry'
import PlaybookManager     from './pages/Admin/PlaybookManager'
import SystemHealth        from './pages/Admin/SystemHealth'

import SecurityMetrics     from './pages/Management/SecurityMetrics'
import AuditTrail          from './pages/Management/AuditTrail'
import ComplianceReports   from './pages/Management/ComplianceReports'

// Role constants
const ROLES = {
  ANALYST:      'ANALYST',
  INVESTIGATOR: 'INVESTIGATOR',
  SYS_ADMIN:    'SYS_ADMIN',
  ORG_MANAGER:  'ORG_MANAGER',
  SUPER_ADMIN:  'SUPER_ADMIN',
}

export default function App() {
  return (
    <AuthProvider>
      <SocketProvider>
        <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Routes>
            {/* Public Routes */}
            <Route path="/"         element={<LandingPage />} />
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/signup"           element={<SignupPage />} />
            <Route path="/register"         element={<SignupPage />} />
            <Route path="/forgot-password"  element={<ForgotPasswordPage />} />
            <Route path="/reset-password"   element={<ResetPasswordPage />} />
            <Route path="/reset-password/:uid/:token" element={<ResetPasswordPage />} />

            {/* Protected Analyst Routes */}
            <Route element={<ProtectedRoute roles={[ROLES.ANALYST, ROLES.SUPER_ADMIN]} />}>
              <Route element={<DashboardLayout />}>
                <Route path="/analyst"                   element={<AnalystDashboard />} />
                <Route path="/analyst/alerts"            element={<AlertFeed />} />
                <Route path="/analyst/alerts/:id"        element={<AlertDetail />} />
                <Route path="/analyst/network-events"    element={<NetworkEvents />} />
                <Route path="/analyst/incidents"         element={<IncidentManager />} />
              </Route>
            </Route>

            {/* Protected Forensics Investigator Routes */}
            <Route element={<ProtectedRoute roles={[ROLES.INVESTIGATOR, ROLES.SUPER_ADMIN]} />}>
              <Route element={<DashboardLayout />}>
                <Route path="/forensics"             element={<CaseManagement />} />
                <Route path="/forensics/evidence"    element={<EvidenceVault />} />
                <Route path="/forensics/timeline/:caseId" element={<ForensicTimeline />} />
              </Route>
            </Route>

            {/* Protected System Admin Routes */}
            <Route element={<ProtectedRoute roles={[ROLES.SYS_ADMIN, ROLES.SUPER_ADMIN]} />}>
              <Route element={<DashboardLayout />}>
                <Route path="/admin"                 element={<AssetRegistry />} />
                <Route path="/admin/playbooks"       element={<PlaybookManager />} />
                <Route path="/admin/health"          element={<SystemHealth />} />
              </Route>
            </Route>

            {/* Protected Org Manager Routes */}
            <Route element={<ProtectedRoute roles={[ROLES.ORG_MANAGER, ROLES.SUPER_ADMIN]} />}>
              <Route element={<DashboardLayout />}>
                <Route path="/org"                   element={<SecurityMetrics />} />
                <Route path="/org/audit"             element={<AuditTrail />} />
                <Route path="/org/reports"           element={<ComplianceReports />} />
              </Route>
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </BrowserRouter>
      </SocketProvider>
    </AuthProvider>
  )
}
