import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navItems = [
    { to: '/overview', label: 'Mission Overview', icon: '🌐' },
    { to: '/citizen', label: 'Citizen Hub', icon: '📍', roles: ['citizen', 'admin'] },
    { to: '/volunteer', label: 'Volunteer Ops', icon: '🦺', roles: ['volunteer', 'admin'] },
    { to: '/command-center', label: 'Incident Command', icon: '🎯', roles: ['admin', 'ngo'] },
    { to: '/copilot', label: 'AI Copilot', icon: '🤖' },
    { to: '/digital-twin', label: 'Digital Twin Sim', icon: '⚡' },
    { to: '/shortage-radar', label: 'Shortage Radar', icon: '📡' },
    { to: '/map', label: 'Disaster Map', icon: '🗺️' },
    { to: '/resources', label: 'Inventory Depot', icon: '📦', roles: ['ngo', 'admin'] },
    { to: '/transparency', label: 'Transparency Journey', icon: '🔍' },
    { to: '/system-health', label: 'DevOps Health', icon: '🩺' },
    { to: '/pitch-deck', label: 'Why ReliefChain?', icon: '🏆' },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-4 hidden md:flex min-h-[calc(100vh-61px)]">
      <div className="space-y-1">
        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
          Operations Navigation
        </div>
        {navItems
          .filter((item) => !item.roles || (user && item.roles.includes(user.role)) || !user)
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3 text-xs text-slate-400">
        <div className="font-bold text-slate-200 mb-1 flex items-center gap-1.5">
          <span>⚡</span> SPHERE Verified
        </div>
        <div>Standardized 15L water & 3 ration packs/person/day calculation engine.</div>
      </div>
    </aside>
  );
};
