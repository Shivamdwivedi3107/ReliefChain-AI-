import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useNotifications } from '../context/NotificationContext';
import { Button, Badge } from '../components/common';

export const Navbar: React.FC = () => {
  const { user, logout, switchDemoRole } = useAuth();
  const { unreadCount } = useNotifications();
  const [notifOpen, setNotifOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur-md border-b border-slate-800 px-4 py-3 flex items-center justify-between">
      <div className="flex items-center gap-6">
        <Link to="/" className="flex items-center gap-2.5 text-slate-100 font-black text-lg tracking-tight">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-slate-950 font-extrabold shadow-lg shadow-cyan-500/20">
            RC
          </div>
          <span>ReliefChain <span className="text-cyan-400">AI</span></span>
        </Link>

        {/* Quick Role Switcher */}
        <div className="hidden lg:flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-lg p-1 text-xs">
          <span className="text-slate-400 px-2 font-semibold">Persona:</span>
          {(['admin', 'volunteer', 'citizen', 'ngo', 'donor'] as const).map((r) => (
            <button
              key={r}
              onClick={() => switchDemoRole(r)}
              className={`px-2.5 py-1 rounded font-medium transition-all ${
                user?.role === r
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow'
                  : 'text-slate-300 hover:text-cyan-400 hover:bg-slate-800'
              }`}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-full text-xs font-semibold text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          LEDGER ONLINE
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="relative p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-cyan-400 transition"
          >
            🔔
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-rose-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </button>
        </div>

        {user ? (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-bold text-slate-200">{user.full_name || user.email}</div>
              <Badge variant="primary" className="text-[10px]">{user.role}</Badge>
            </div>
            <Button variant="outline" size="sm" onClick={logout}>Sign Out</Button>
          </div>
        ) : (
          <Link to="/login">
            <Button variant="primary" size="sm">Sign In</Button>
          </Link>
        )}
      </div>
    </header>
  );
};
