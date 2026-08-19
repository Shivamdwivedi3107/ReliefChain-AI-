import React, { useEffect, useState } from 'react';
import { Card, StatCard, Badge, Button } from '../components/common';
import { dashboardService, reliefService } from '../services';
import { ReliefRequest } from '../types';

export const CitizenDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sosModalOpen, setSosModalOpen] = useState<boolean>(false);
  const [peopleCount, setPeopleCount] = useState<number>(4);
  const [medicalNeeded, setMedicalNeeded] = useState<boolean>(true);
  const [waterNeeded, setWaterNeeded] = useState<boolean>(true);
  const [foodNeeded, setFoodNeeded] = useState<boolean>(true);
  const [shelterNeeded, setShelterNeeded] = useState<boolean>(false);
  const [disasterType, setDisasterType] = useState<string>('flood');
  const [triageForecast, setTriageForecast] = useState<any>({ priority: 'Critical', score: 85, reason: 'High triage severity' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await dashboardService.getCitizenDashboard();
      setData(res);
    } catch (err) {
      console.error('Failed to load citizen dashboard', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriagePreview = async (people: number, med: boolean, type: string) => {
    try {
      const res = await reliefService.quickTriage({
        people_count: people,
        has_medical_emergency: med,
        disaster_type: type,
        supplies_needed: [med ? 'medical' : '', waterNeeded ? 'water' : '', foodNeeded ? 'food' : ''].filter(Boolean),
      });
      setTriageForecast(res);
    } catch (e) {
      // fallback
    }
  };

  const handleSosSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await reliefService.createRequest({
        disaster_type: disasterType,
        people_count: peopleCount,
        latitude: 19.0760,
        longitude: 72.8777,
        description: 'Urgent emergency rescue and relief package request from resident.',
        medical_urgency: medicalNeeded ? 'Urgent' : 'None',
        vulnerable_individuals: medicalNeeded ? 1 : 0,
        items_needed: [medicalNeeded ? 'Medical Kit' : '', waterNeeded ? 'Potable Water' : '', foodNeeded ? 'Food Pack' : ''].filter(Boolean),
      });
      setSosModalOpen(false);
      loadData();
    } catch (err) {
      alert('Failed to submit SOS request');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>📍</span> Citizen Emergency Hub
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time SOS distress status, verified evacuation shelters, and instant triage dispatch.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="danger" size="md" onClick={() => setSosModalOpen(true)}>
            🚨 One-Tap Emergency SOS
          </Button>
          <Button variant="outline" size="md" onClick={loadData}>↻ Refresh</Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Active SOS Distress Requests"
          value={data?.my_active_requests?.length || 0}
          subtitle="Monitored in emergency intake queue"
          borderColor="border-l-rose-500"
          icon="🚨"
        />
        <StatCard
          title="Nearby Safe Evacuation Shelters"
          value={data?.safe_evacuation_zones?.length || 3}
          subtitle="High-ground verified relief centers"
          borderColor="border-l-emerald-500"
          icon="🛡️"
        />
        <StatCard
          title="Aid Deliveries Received"
          value={data?.my_distributions?.length || 0}
          subtitle="QR-verified physical handovers"
          borderColor="border-l-cyan-500"
          icon="📦"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Active Requests */}
        <div className="lg:col-span-2 space-y-4">
          <Card title="📋 My Emergency Relief Requests" subtitle="Real-time lifecycle & AI priority scoring">
            {loading ? (
              <div className="text-center py-8 text-slate-400 text-xs">Loading requests...</div>
            ) : !data?.my_active_requests?.length ? (
              <div className="text-center py-10 bg-slate-950/40 rounded-lg border border-slate-800/80">
                <div className="text-2xl mb-2">🛡️</div>
                <div className="text-sm font-semibold text-slate-300">No Active SOS Requests</div>
                <div className="text-xs text-slate-500 mt-1">Your registered sector is currently clear of open distress intakes.</div>
              </div>
            ) : (
              <div className="space-y-3">
                {data.my_active_requests.map((r: ReliefRequest) => (
                  <div key={r.id} className="bg-slate-950/70 border border-slate-800 rounded-lg p-4 flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold text-slate-200 uppercase">{r.disaster_type} Distress</span>
                        <Badge variant={r.priority === 'Critical' ? 'danger' : 'warning'}>{r.priority}</Badge>
                      </div>
                      <p className="text-xs text-slate-400">{r.urgency_description || 'Essential supplies needed'}</p>
                      <div className="text-[11px] text-slate-500 mt-2">People in Danger: {r.affected_people} • Status: {r.status.toUpperCase()}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right: Safe Shelters & Nearby Hazards */}
        <div className="space-y-6">
          <Card title="🛡️ Safe Evacuation Hubs" subtitle="Capacity & emergency supply status">
            <div className="space-y-2.5">
              {(data?.safe_evacuation_zones || [
                { name: 'Central High School Gym Hub', capacity: '450 evacuees', status: 'OPEN' },
                { name: 'North Delta Community Relief Dome', capacity: '300 evacuees', status: 'OPEN' },
              ]).map((z: any, idx: number) => (
                <div key={idx} className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-3 flex justify-between items-center">
                  <div>
                    <div className="text-xs font-bold text-emerald-400">{z.name}</div>
                    <div className="text-[11px] text-slate-400">{z.capacity} • Water & Medical Available</div>
                  </div>
                  <Badge variant="success" className="text-[10px]">VERIFIED</Badge>
                </div>
              ))}
            </div>
          </Card>

          <Card title="⚠️ Nearby Monitored Hazards" subtitle="Live proximity radar">
            <div className="space-y-2">
              {(data?.nearby_incidents || [
                { title: 'Monsoon Flash Inundation Sector 4', severity: 8.5 },
              ]).map((h: any, i: number) => (
                <div key={i} className="flex justify-between items-center text-xs py-1.5 border-b border-slate-800/60 last:border-0">
                  <span className="text-slate-300">{h.title}</span>
                  <Badge variant="danger" className="text-[10px]">Sev {h.severity}/10</Badge>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* One-Tap SOS Modal */}
      {sosModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-lg font-black text-rose-400 flex items-center gap-2">
                <span>🚨</span> One-Tap Emergency SOS
              </h3>
              <button onClick={() => setSosModalOpen(false)} className="text-slate-400 hover:text-slate-100">&times;</button>
            </div>

            {/* AI Triage Forecast Preview */}
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-slate-300">Live AI Priority Forecast:</span>
                <Badge variant="danger">{triageForecast.priority.toUpperCase()} (Score: {triageForecast.score || 85}/100)</Badge>
              </div>
              <p className="text-xs text-slate-300 mt-1">{triageForecast.reason || 'High severity intake'}</p>
            </div>

            <form onSubmit={handleSosSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-400 mb-1">Disaster Hazard Type</label>
                <select
                  value={disasterType}
                  onChange={(e) => {
                    setDisasterType(e.target.value);
                    handleTriagePreview(peopleCount, medicalNeeded, e.target.value);
                  }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200"
                >
                  <option value="flood">Flood / Cyclone Inundation</option>
                  <option value="earthquake">Earthquake / Structural Collapse</option>
                  <option value="wildfire">Wildfire / Heat Hazard</option>
                </select>
              </div>

              <div>
                <div className="flex justify-between text-slate-400 mb-1">
                  <span>People in Danger</span>
                  <span className="font-bold text-rose-400">{peopleCount} Persons</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="25"
                  value={peopleCount}
                  onChange={(e) => {
                    const val = parseInt(e.target.value);
                    setPeopleCount(val);
                    handleTriagePreview(val, medicalNeeded, disasterType);
                  }}
                  className="w-full"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <label className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
                  <input
                    type="checkbox"
                    checked={medicalNeeded}
                    onChange={(e) => {
                      setMedicalNeeded(e.target.checked);
                      handleTriagePreview(peopleCount, e.target.checked, disasterType);
                    }}
                  />
                  <span>🩺 Medical Care</span>
                </label>
                <label className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
                  <input type="checkbox" checked={waterNeeded} onChange={(e) => setWaterNeeded(e.target.checked)} />
                  <span>💧 Potable Water</span>
                </label>
                <label className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
                  <input type="checkbox" checked={foodNeeded} onChange={(e) => setFoodNeeded(e.target.checked)} />
                  <span>🍞 Food Packs</span>
                </label>
                <label className="flex items-center gap-2 p-2 bg-slate-950/60 rounded border border-slate-800">
                  <input type="checkbox" checked={shelterNeeded} onChange={(e) => setShelterNeeded(e.target.checked)} />
                  <span>⛺ Evacuation Tent</span>
                </label>
              </div>

              <Button variant="danger" size="lg" className="w-full">
                🚨 DISPATCH IMMEDIATE SOS DISTRESS
              </Button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
