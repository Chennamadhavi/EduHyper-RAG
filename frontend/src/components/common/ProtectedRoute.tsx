import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import LoadingState from './LoadingState';

export interface ProtectedRouteProps {
  allowedRoles?: ('teacher' | 'student')[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles }) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingState message="Validating authentication session..." size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  // Check role-based access control
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to user's assigned dashboard
    const fallbackPath = user.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard';
    return <Navigate to={fallbackPath} replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
