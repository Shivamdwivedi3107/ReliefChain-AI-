import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, Button } from '../components/common';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, switchDemoRole } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Invalid credentials');
    }
  };

  const handleDemoClick = async (role: any) => {
    await switchDemoRole(role);
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-8 space-y-6">
        <div className="text-center">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-600 flex items-center justify-center text-slate-950 font-black text-xl mx-auto mb-3 shadow-lg shadow-cyan-500/25">
            RC
          </div>
          <h2 className="text-2xl font-black text-slate-100">Sign In to ReliefChain AI</h2>
          <p className="text-xs text-slate-400 mt-1">Humanitarian Command & Relief Coordination Platform</p>
        </div>

        {error && <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400 text-xs font-semibold">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-cyan-400"
              placeholder="user@reliefchain.ai"
              required
            />
          </div>
          <div>
            <label className="block text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-100 focus:outline-none focus:border-cyan-400"
              placeholder="••••••••••••"
              required
            />
          </div>
          <Button variant="primary" size="lg" className="w-full">Sign In</Button>
        </form>

        {/* 1-Click Demo Login Personas */}
        <div className="border-t border-slate-800/80 pt-4">
          <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 text-center">Instant Demo Personas:</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Button variant="outline" size="sm" onClick={() => handleDemoClick('admin')}>🔑 Admin</Button>
            <Button variant="outline" size="sm" onClick={() => handleDemoClick('volunteer')}>🦺 Volunteer</Button>
            <Button variant="outline" size="sm" onClick={() => handleDemoClick('citizen')}>📍 Citizen</Button>
            <Button variant="outline" size="sm" onClick={() => handleDemoClick('ngo')}>🏢 Relief NGO</Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
