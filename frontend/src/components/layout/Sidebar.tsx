import React from 'react';
import { NavLink, Link, useLocation } from 'react-router-dom';
import {
  Network,
  LayoutDashboard,
  BookOpen,
  FileText,
  Users,
  BarChart3,
  Settings,
  Bot,
  History,
  TrendingUp,
  X,
  ArrowLeftRight,
} from 'lucide-react';
import { UserRole, NavItem } from '../../types/navigation';

export interface SidebarProps {
  role: UserRole;
  onRoleSwitch?: (newRole: UserRole) => void;
  isOpen?: boolean;
  onClose?: () => void;
}

export const teacherNavItems: NavItem[] = [
  { title: 'Dashboard', path: '/teacher/dashboard', icon: LayoutDashboard },
  { title: 'My Courses', path: '/teacher/courses', icon: BookOpen },
  { title: 'Documents', path: '/teacher/documents', icon: FileText },
  { title: 'Student Management', path: '/teacher/students', icon: Users },
  { title: 'Hypergraph Explorer', path: '/teacher/hypergraph', icon: Network },
  { title: 'Analytics', path: '/teacher/analytics', icon: BarChart3 },
  { title: 'Settings', path: '/teacher/settings', icon: Settings },
];

export const studentNavItems: NavItem[] = [
  { title: 'Dashboard', path: '/student/dashboard', icon: LayoutDashboard },
  { title: 'My Courses', path: '/student/courses', icon: BookOpen },
  { title: 'AI Tutor', path: '/student/tutor', icon: Bot },
  { title: 'Chat History', path: '/student/history', icon: History },
  { title: 'Learning Progress', path: '/student/progress', icon: TrendingUp },
  { title: 'Settings', path: '/student/settings', icon: Settings },
];

export const Sidebar: React.FC<SidebarProps> = ({
  role,
  onRoleSwitch,
  isOpen = false,
  onClose,
}) => {
  const location = useLocation();
  const navItems = role === 'teacher' ? teacherNavItems : studentNavItems;

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 text-slate-300 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-slate-800/80">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-sm">
              <Network className="w-4 h-4" />
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight">
                EduHyper<span className="text-blue-500">RAG</span>
              </span>
              <span className="block text-[10px] text-slate-400 font-medium -mt-1 uppercase tracking-wider">
                {role === 'teacher' ? 'Teacher Portal' : 'Student Portal'}
              </span>
            </div>
          </Link>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Role toggle badge preview for development/previewing */}
        <div className="px-4 py-3 bg-slate-950/40 border-b border-slate-800/60">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Active Workspace</span>
            <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
              {role}
            </span>
          </div>
          {onRoleSwitch && (
            <button
              onClick={() => onRoleSwitch(role === 'teacher' ? 'student' : 'teacher')}
              className="mt-2 w-full flex items-center justify-center gap-1.5 text-xs text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 py-1.5 px-2 rounded border border-slate-700/70 transition-colors"
            >
              <ArrowLeftRight className="w-3.5 h-3.5" /> Switch to {role === 'teacher' ? 'Student' : 'Teacher'} View
            </button>
          )}
        </div>

        {/* Nav list */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`w-4 h-4 transition-colors ${
                      isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'
                    }`}
                  />
                  <span>{item.title}</span>
                </div>
                {item.badge && (
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                    {item.badge}
                  </span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom footer status */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Pipeline Engine</span>
            <span className="flex items-center gap-1 text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              v1.0.0
            </span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
