import React, { useEffect, useState } from 'react';
import { Card, StatCard, Badge, Button } from '../components/common';
import { dashboardService } from '../services';

export const VolunteerDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await dashboardService.getVolunteerDashboard();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const profile = data?.volunteer_profile || {
    name: 'Phase 11 Volunteer Responder',
    skills: ['First Aid', 'Boat Rescue', 'Communications'],
    max_capacity: 4,
    current_active_missions: 1,
    reliability_score: 0.96,
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🦺</span> Volunteer Operations Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            4-Factor AI mission matching, field delivery confirmation, and workload capacity management.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="primary" size="md">
            📷 Scan Delivery QR Token
          </Button>
          <Button variant="outline" size="md" onClick={loadData}>↻ Refresh</Button>
        </div>
      </div>

      {/* Volunteer KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <StatCard
          title="Responder Profile"
          value={profile.name}
          subtitle={(profile.skills || []).join(', ')}
          borderColor="border-l-cyan-500"
          icon="🦺"
        />
        <StatCard
          title="Workload Capacity"
          value={`${profile.current_active_missions} / ${profile.max_capacity} Missions`}
          subtitle="25% active field workload"
          borderColor="border-l-amber-500"
          icon="⚡"
        />
        <StatCard
          title="Reliability Score"
          value={`${Math.round(profile.reliability_score * 100)}%`}
          subtitle="Verified deliveries sealed"
          borderColor="border-l-emerald-500"
          icon="🛡️"
        />
        <StatCard
          title="Completed Missions"
          value={profile.completed_missions_count || 14}
          subtitle="All-time deliveries verified"
          borderColor="border-l-purple-500"
          icon="🏆"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Active Assigned Missions */}
        <Card title="🎯 My Active Assigned Missions" subtitle="Current active field queue">
          {loading ? (
            <div className="text-center py-8 text-xs text-slate-400">Loading missions...</div>
          ) : !data?.assigned_missions?.length ? (
            <div className="text-center py-10 bg-slate-950/40 rounded-lg border border-slate-800/80">
              <div className="text-2xl mb-2">🎯</div>
              <div className="text-sm font-semibold text-slate-300">No Active Missions Assigned</div>
              <div className="text-xs text-slate-500 mt-1">Accept an AI recommended mission below to start field operations.</div>
            </div>
          ) : (
            <div className="space-y-3">
              {data.assigned_missions.map((m: any) => (
                <div key={m.id} className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex justify-between items-center">
                  <div>
                    <div className="text-sm font-bold text-slate-200">{m.title}</div>
                    <div className="text-xs text-slate-400 mt-0.5">{m.description}</div>
                    <div className="text-[11px] text-slate-500 mt-2">Status: <strong className="text-cyan-400">{m.status}</strong></div>
                  </div>
                  <Button variant="primary" size="sm">Verify QR Delivery</Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Right: AI Recommended Missions */}
        <Card title="🧠 AI Recommended Missions" subtitle="Multi-criteria weighted ranking (Distance, Skills, Capacity, Reliability)">
          <div className="space-y-3">
            {(data?.recommended_missions || [
              { mission_title: 'Flood Rescue & Potable Water Delivery Sector 4', match_score: 0.94, match_reasons: ['First Aid skill certified', '2.4km from ground zero', 'Workload capacity available'] },
              { mission_title: 'Medical Evacuation Support North Delta', match_score: 0.88, match_reasons: ['Boat rescue expertise', 'High priority life-safety sector'] },
            ]).map((rm: any, i: number) => (
              <div key={i} className="bg-slate-950/70 border border-emerald-500/20 border-l-4 border-l-emerald-500 rounded-lg p-4">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-bold text-slate-200">{rm.mission_title}</span>
                  <Badge variant="success" className="font-extrabold">{Math.round(rm.match_score * 100)}% AI MATCH</Badge>
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  {(rm.match_reasons || []).join(' • ')}
                </div>
                <div className="flex justify-between items-center mt-3 pt-2 border-t border-slate-800/60">
                  <span className="text-[11px] text-slate-500">Proximity: ~2.4 km away</span>
                  <Button variant="outline" size="sm">Accept Dispatch</Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
