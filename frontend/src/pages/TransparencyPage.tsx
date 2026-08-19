import React, { useEffect, useState } from 'react';
import { Card, Badge, Button } from '../components/common';
import { dashboardService } from '../services';

export const TransparencyPage: React.FC = () => {
  const [journeys, setJourneys] = useState<any[]>([]);
  const [selectedJourney, setSelectedJourney] = useState<any>(null);
  const [searchRef, setSearchRef] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const list = await dashboardService.getLatestJourneys();
      setJourneys(list);
      if (list?.length > 0) {
        loadJourney(list[0].reference_id);
      }
    } catch (e) {
      console.warn(e);
    }
  };

  const loadJourney = async (ref: string) => {
    try {
      const j = await dashboardService.getTransparencyJourney(ref);
      setSelectedJourney(j);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🔍</span> Public Transparency Journey
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Trace humanitarian aid from donor contribution to on-chain ledger block and single-use QR verification.
          </p>
        </div>
        <Badge variant="primary">SHA-256 PROOF-OF-DELIVERY</Badge>
      </div>

      {/* Search */}
      <Card>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (searchRef) loadJourney(searchRef);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={searchRef}
            onChange={(e) => setSearchRef(e.target.value)}
            placeholder="Enter Donation ID, Mission Ref, or Transaction Hash..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-400"
          />
          <Button variant="primary" size="md">Trace Aid Journey</Button>
        </form>
      </Card>

      {/* 6-Stage Roadmap */}
      {selectedJourney && (
        <Card title={`🚀 Verifiable Aid Delivery Pipeline: ${selectedJourney.reference_id}`} subtitle="Sequential cryptographic verification stages">
          <div className="space-y-4 my-2">
            {selectedJourney.stages?.map((s: any, idx: number) => (
              <div key={idx} className="flex gap-4 items-start">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                  s.completed ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/25' : 'bg-slate-800 text-slate-400'
                }`}>
                  {s.completed ? '✓' : idx + 1}
                </div>
                <div className="flex-1 bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">{s.stage_name}</span>
                    <span className="text-[10px] text-slate-500">{s.timestamp ? new Date(s.timestamp).toLocaleDateString() : 'Verified Sequence'}</span>
                  </div>
                  <p className="text-slate-400 mt-1">{s.details}</p>
                  {s.sha256_hash && (
                    <div className="text-[10px] font-mono text-emerald-400 mt-1.5 break-all">
                      SHA-256 Block: {s.sha256_hash}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
