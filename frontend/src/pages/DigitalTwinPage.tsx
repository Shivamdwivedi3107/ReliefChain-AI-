import React, { useState } from 'react';
import { Card, StatCard, Badge, Button } from '../components/common';

export const DigitalTwinPage: React.FC = () => {
  const [hazardType, setHazardType] = useState('cyclone');
  const [severity, setSeverity] = useState(8.5);
  const [population, setPopulation] = useState(15000);
  const [duration, setDuration] = useState(24);

  // SPHERE Calculations
  const days = duration / 24;
  const waterNeed = Math.round(population * 15 * days * (severity / 7.0));
  const foodNeed = Math.round(population * 3 * days * (severity / 7.0));
  const medNeed = Math.round(population * 0.05 * (severity / 6.0));
  const volNeed = Math.round((population / 125) * (severity / 6.0));

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🌐</span> Disaster Digital Twin Simulator
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Interactive contingency scenario modeler projecting multi-hazard timelines and SPHERE resource burn rates.
          </p>
        </div>
        <Badge variant="primary">SIMULATION SANDBOX</Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls */}
        <Card title="⚙️ Scenario Parameters" subtitle="Adjust real-time disaster variables">
          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Hazard Type</label>
              <select
                value={hazardType}
                onChange={(e) => setHazardType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-slate-200"
              >
                <option value="cyclone">Category 4 Tropical Cyclone</option>
                <option value="flood">Flash Flood / River Inundation</option>
                <option value="earthquake">Magnitude 7.2 Crustal Earthquake</option>
                <option value="wildfire">Fast-Moving Scrub Wildfire</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Severity Index</span>
                <span className="font-bold text-rose-400">{severity} / 10.0</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="10.0"
                step="0.5"
                value={severity}
                onChange={(e) => setSeverity(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Affected Population</span>
                <span className="font-bold text-cyan-400">{population.toLocaleString()}</span>
              </div>
              <input
                type="range"
                min="500"
                max="50000"
                step="500"
                value={population}
                onChange={(e) => setPopulation(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Simulation Horizon</span>
                <span className="font-bold text-purple-400">{duration} Hours</span>
              </div>
              <input
                type="range"
                min="6"
                max="72"
                step="6"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <Button variant="primary" size="md" className="w-full mt-2">
              ⚡ Recalculate Model
            </Button>
          </div>
        </Card>

        {/* Results & Milestones */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="📊 Projected Relief Demand (SPHERE Standard)" subtitle="Calculated supply thresholds">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <StatCard title="Potable Water" value={`${waterNeed.toLocaleString()} L`} borderColor="border-l-cyan-500" icon="💧" />
              <StatCard title="Food Rations" value={foodNeed.toLocaleString()} borderColor="border-l-amber-500" icon="🍞" />
              <StatCard title="Trauma Kits" value={medNeed.toLocaleString()} borderColor="border-l-rose-500" icon="🩺" />
              <StatCard title="Responders" value={volNeed.toLocaleString()} borderColor="border-l-purple-500" icon="🦺" />
            </div>
          </Card>

          <Card title="⏱️ Response Timeline Milestones" subtitle="Hour-by-hour operational roadmap">
            <div className="space-y-3 text-xs">
              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <Badge variant="danger" className="min-w-[65px] text-center">Hour 0-2</Badge>
                <span className="text-slate-300">Initial impact. Random Forest triage classifies critical medical cases; high-ground shelters opened.</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <Badge variant="warning" className="min-w-[65px] text-center">Hour 6</Badge>
                <span className="text-slate-300">First convoy wave: {(waterNeed * 0.35).toFixed(0)} L potable water & {Math.round(foodNeed * 0.35)} rations allocated at depot.</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <Badge variant="primary" className="min-w-[65px] text-center">Hour 12</Badge>
                <span className="text-slate-300">{volNeed} field volunteers dispatched with cryptographic QR tokens. Evacuation shelters fully staffed.</span>
              </div>
              <div className="flex items-start gap-3 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                <Badge variant="success" className="min-w-[65px] text-center">Hour 24</Badge>
                <span className="text-slate-300">Perimeter stabilized. 100% handover transactions sealed to SHA-256 transparent audit ledger.</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};
