import React, { useEffect, useState } from 'react';
import { Card, StatCard, Badge, Button } from '../components/common';
import { dashboardService } from '../services';

export const AdminCommandCenter: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await dashboardService.getCommandCenterSummary();
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🎯</span> Incident Command Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time multi-hazard threat grid, active SITREPs, and operational decision support.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="primary" size="md" onClick={() => alert('New Incident modal')}>
            + Declare Incident
          </Button>
          <Button variant="outline" size="md" onClick={loadData}>↻ Refresh Telemetry</Button>
        </div>
      </div>

      {loading && (
        <div className="text-xs text-cyan-400 font-semibold flex items-center gap-2 bg-slate-900/60 border border-cyan-500/20 px-3 py-2 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
          Refreshing operational telemetry...
        </div>
      )}

      {/* Top Threat KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <StatCard
          title="Active Hazards"
          value={data?.active_incidents_count || 3}
          subtitle="Monitored impact perimeters"
          borderColor="border-l-rose-500"
          icon="🚨"
        />
        <StatCard
          title="Critical Intake SOS"
          value={data?.pending_requests_count || 12}
          subtitle="Priority 1 triage cases"
          borderColor="border-l-amber-500"
          icon="⚠️"
        />
        <StatCard
          title="Deployed Volunteers"
          value={data?.active_volunteers_count || 24}
          subtitle="Field squads operating"
          borderColor="border-l-emerald-500"
          icon="🦺"
        />
        <StatCard
          title="Field SITREPs"
          value={data?.latest_sitreps?.length || 5}
          subtitle="Reconnaissance logs verified"
          borderColor="border-l-cyan-500"
          icon="📋"
        />
      </div>

      {/* Main Grid: Active Threat List & Live Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <Card title="🚨 Active Disaster Incidents" subtitle="Operational status, severity index & escalation level">
            <div className="space-y-3">
              {(data?.active_incidents || [
                { title: 'Monsoon Flash Inundation Sector 4', disaster_type: 'flood', severity: 8.8, escalation_level: 'LEVEL_4_CRITICAL', status: 'ACTIVE' },
                { title: 'Coastal Cyclone Category-3 Warning', disaster_type: 'cyclone', severity: 7.4, escalation_level: 'LEVEL_3_HIGH', status: 'MONITORING' },
              ]).map((inc: any, i: number) => (
                <div key={i} className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex justify-between items-center">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-bold text-slate-200">{inc.title}</span>
                      <Badge variant={inc.escalation_level.includes('CRITICAL') ? 'danger' : 'warning'}>
                        {inc.escalation_level}
                      </Badge>
                    </div>
                    <div className="text-xs text-slate-400">
                      Disaster: <strong className="text-cyan-400 uppercase">{inc.disaster_type}</strong> • Severity: <strong>{inc.severity}/10</strong>
                    </div>
                  </div>
                  <Button variant="outline" size="sm">Inspect Incident</Button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div>
          <Card title="⚡ Live Command Telemetry" subtitle="Recent timeline & SITREP records">
            <div className="space-y-3">
              {(data?.latest_sitreps || [
                { report_type: 'field', summary: 'Bridge 4 impassable; floodwaters 1.2m above levee.', infrastructure_damage_level: 'severe' },
                { report_type: 'medical', summary: 'Field triage hub established at Sector 2 high school.', infrastructure_damage_level: 'moderate' },
              ]).map((s: any, idx: number) => (
                <div key={idx} className="bg-slate-950/50 border border-slate-800 rounded-lg p-3 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <strong className="text-cyan-400 uppercase">{s.report_type} SITREP</strong>
                    <Badge variant="outline" className="text-[10px]">{s.infrastructure_damage_level}</Badge>
                  </div>
                  <p className="text-slate-300">{s.summary}</p>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
