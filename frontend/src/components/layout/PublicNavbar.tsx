import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Network, Menu, X, ArrowRight, LayoutDashboard, LogOut } from 'lucide-react';
import Button from '../common/Button';
import { useAuth } from '../../hooks/useAuth';

export const PublicNavbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'Features', path: '/#features' },
    { label: 'How It Works', path: '/#how-it-works' },
  ];

  const dashboardPath = user?.role === 'teacher' ? '/teacher/dashboard' : '/student/dashboard';

  return (
    <header className="sticky top-0 z-40 w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm group-hover:bg-blue-700 transition-colors">
              <Network className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight flex items-center">
                EduHyper<span className="text-blue-600">RAG</span>
              </span>
              <span className="block text-[10px] text-slate-500 font-medium -mt-1 tracking-wider uppercase">
                Hypergraph AI Tutor
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {navLinks.map((link) => (
              <a
                key={link.path}
                href={link.path}
                className="text-sm font-medium text-slate-600 hover:text-blue-600 transition-colors"
              >
                {link.label}
              </a>
            ))}
          </nav>

          {/* Action Buttons */}
          <div className="hidden md:flex items-center space-x-3">
            {isAuthenticated && user ? (
              <>
                <Link to={dashboardPath}>
                  <Button variant="primary" size="sm" leftIcon={<LayoutDashboard className="w-4 h-4" />}>
                    {user.role === 'teacher' ? 'Teacher Dashboard' : 'Student Dashboard'}
                  </Button>
                </Link>
                <Button variant="ghost" size="sm" onClick={logout} title="Sign Out">
                  <LogOut className="w-4 h-4 text-slate-500" />
                </Button>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost" size="sm">
                    Log In
                  </Button>
                </Link>
                <Link to="/register">
                  <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-200 bg-white px-4 pt-2 pb-4 space-y-3 shadow-lg">
          {navLinks.map((link) => (
            <a
              key={link.path}
              href={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:text-blue-600 hover:bg-slate-50"
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3 border-t border-slate-100 flex flex-col gap-2">
            {isAuthenticated && user ? (
              <>
                <Link to={dashboardPath} onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" size="sm" className="w-full">
                    {user.role === 'teacher' ? 'Teacher Dashboard' : 'Student Dashboard'}
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                >
                  Log Out
                </Button>
              </>
            ) : (
              <>
                <Link to="/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" size="sm" className="w-full">
                    Log In
                  </Button>
                </Link>
                <Link to="/register" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="primary" size="sm" className="w-full">
                    Get Started
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};

export default PublicNavbar;
