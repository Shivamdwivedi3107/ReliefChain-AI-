import React from 'react';

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'outline';
  size?: 'sm' | 'md' | 'lg';
}> = ({ variant = 'primary', size = 'md', className = '', children, ...props }) => {
  const baseClasses = 'inline-flex items-center justify-center font-semibold rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  }[size];

  const variantClasses = {
    primary: 'bg-cyan-500 hover:bg-cyan-600 text-slate-950 font-bold focus:ring-cyan-400 shadow-lg shadow-cyan-500/20',
    secondary: 'bg-slate-800 hover:bg-slate-700 text-slate-100 focus:ring-slate-500 border border-slate-700',
    danger: 'bg-rose-500 hover:bg-rose-600 text-white font-bold focus:ring-rose-400 shadow-lg shadow-rose-500/25',
    success: 'bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold focus:ring-emerald-400',
    outline: 'border border-slate-700 hover:border-cyan-400 text-slate-200 hover:text-cyan-400 bg-transparent',
  }[variant];

  return (
    <button className={`${baseClasses} ${sizeClasses} ${variantClasses} ${className}`} {...props}>
      {children}
    </button>
  );
};

export const Card: React.FC<{
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}> = ({ title, subtitle, action, className = '', children }) => {
  return (
    <div className={`bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-xl p-5 shadow-xl ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4 border-b border-slate-800/80 pb-3">
          <div>
            {title && <h3 className="text-base font-bold text-slate-100">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};

export const Badge: React.FC<{
  variant?: 'danger' | 'warning' | 'success' | 'primary' | 'outline';
  children: React.ReactNode;
  className?: string;
}> = ({ variant = 'primary', children, className = '' }) => {
  const variantClasses = {
    danger: 'bg-rose-500/15 text-rose-400 border border-rose-500/30',
    warning: 'bg-amber-500/15 text-amber-400 border border-amber-500/30',
    success: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30',
    primary: 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30',
    outline: 'border border-slate-700 text-slate-300',
  }[variant];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider ${variantClasses} ${className}`}>
      {children}
    </span>
  );
};

export const StatCard: React.FC<{
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: string;
  borderColor?: string;
}> = ({ title, value, subtitle, icon, trend, borderColor = 'border-l-cyan-500' }) => {
  return (
    <div className={`bg-slate-900/80 backdrop-blur-md border border-slate-800 border-l-4 ${borderColor} rounded-xl p-4 shadow-lg flex flex-col justify-between`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</span>
        {icon && <div className="text-lg opacity-80">{icon}</div>}
      </div>
      <div className="my-2">
        <div className="text-2xl font-black text-slate-100 tracking-tight">{value}</div>
        {subtitle && <div className="text-xs text-slate-400 mt-0.5">{subtitle}</div>}
      </div>
      {trend && <div className="text-xs text-emerald-400 font-semibold">{trend}</div>}
    </div>
  );
};
