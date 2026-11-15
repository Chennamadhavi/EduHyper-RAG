import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import Navbar from '../components/layout/Navbar';
import { UserRole } from '../types/navigation';

export interface AppLayoutProps {
  initialRole?: UserRole;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ initialRole }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Derive role based on URL route or initialRole
  const currentRole: UserRole = location.pathname.startsWith('/teacher')
    ? 'teacher'
    : location.pathname.startsWith('/student')
    ? 'student'
    : initialRole || 'student';

  // Handle switching views between teacher and student
  const handleRoleSwitch = (newRole: UserRole) => {
    if (newRole === 'teacher') {
      navigate('/teacher/dashboard');
    } else {
      navigate('/student/dashboard');
    }
  };

  // Close sidebar automatically on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex">
      {/* Sidebar */}
      <Sidebar
        role={currentRole}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onRoleSwitch={handleRoleSwitch}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64 transition-all duration-300">
        <Navbar
          role={currentRole}
          onMenuToggle={() => setSidebarOpen((prev) => !prev)}
        />

        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
