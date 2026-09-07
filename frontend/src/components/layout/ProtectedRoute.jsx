import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

// Role-to-default-path mapping for redirect after login
const ROLE_DEFAULT_PATHS = {
  ANALYST:      '/analyst',
  INVESTIGATOR: '/forensics',
  SYS_ADMIN:    '/admin',
  ORG_MANAGER:  '/org',
  SUPER_ADMIN:  '/analyst',
}

export const getRoleDefaultPath = (role) => ROLE_DEFAULT_PATHS[role] || '/login'

export default function ProtectedRoute({ roles = [] }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-navy-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-cyber-cyan border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-400 text-sm font-mono">Authenticating...</span>
        </div>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />

  if (roles.length > 0 && !roles.includes(user.role)) {
    // Redirect to user's appropriate dashboard
    return <Navigate to={getRoleDefaultPath(user.role)} replace />
  }

  return <Outlet />
}
