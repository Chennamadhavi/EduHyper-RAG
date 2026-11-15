import React from 'react';
import { Menu, Search, Bell, User, ExternalLink, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { UserRole } from '../../types/navigation';
import { useAuth } from '../../hooks/useAuth';

export interface NavbarProps {
  role: UserRole;
  onMenuToggle: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ role, onMenuToggle }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-white border-b border-slate-200/80 px-4 sm:px-6 lg:px-8 flex items-center justify-between shadow-xs">
      {/* Left: Mobile hamburger & Search input */}
      <div className="flex items-center gap-3 sm:gap-4 flex-1 max-w-lg">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 lg:hidden focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative w-full max-w-xs sm:max-w-md hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            placeholder="Search courses, documents, or concepts..."
            className="w-full pl-9 pr-4 py-1.5 text-xs sm:text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
            disabled
            title="Search will be activated in subsequent integration steps"
          />
        </div>
      </div>

      {/* Right: Quick actions, notifications, profile */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Link back to public landing page */}
        <Link
          to="/"
          className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-600 hover:text-blue-600 hover:bg-slate-50 rounded-lg border border-slate-200 transition-colors"
          title="Return to public portal"
        >
          <span>Home</span>
          <ExternalLink className="w-3 h-3" />
        </Link>

        {/* Notifications placeholder */}
        <div className="relative">
          <button
            type="button"
            className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 relative focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="View notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-blue-600" />
          </button>
        </div>

        {/* Authenticated user profile */}
        <div className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-300 flex items-center justify-center text-blue-700 font-bold text-xs uppercase">
            {user ? user.username.charAt(0) : <User className="w-4 h-4" />}
          </div>
          <div className="hidden md:block text-left">
            <div className="text-xs font-semibold text-slate-800">
              {user ? user.username : (role === 'teacher' ? 'Instructor' : 'Student')}
            </div>
            <div className="text-[10px] text-slate-500 font-medium capitalize">
              {user ? `${user.role} Account` : 'Guest Session'}
            </div>
          </div>

          {/* Logout Action */}
          {user && (
            <button
              onClick={handleLogout}
              className="ml-1 p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Sign Out"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
