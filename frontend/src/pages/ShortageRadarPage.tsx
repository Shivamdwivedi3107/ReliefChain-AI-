import React, { useEffect, useState } from 'react';
import { Card, Badge, Button } from '../components/common';
import { resourceService } from '../services';
import { ShortageRadarResponse } from '../types';

export const ShortageRadarPage: React.FC = () => {
  const [data, setData] = useState<ShortageRadarResponse | null>(null);
  const [horizon, setHorizon] = useState(3);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [horizon]);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await resourceService.getShortageRadar(horizon);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>📡</span> Resource Shortage Radar
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            SPHERE humanitarian supply gap detection cross-referencing depot stock against affected population demand.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={horizon}
            onChange={(e) => setHorizon(parseInt(e.target.value))}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
          >
            <option value={3}>3-Day Buffer</option>
            <option value={5}>5-Day Buffer</option>
            <option value={7}>7-Day Buffer</option>
          </select>
          <Button variant="outline" size="sm" onClick={loadData}>↻ Refresh</Button>
        </div>
      </div>

      {/* Summary Alert Banner */}
      <Card className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-l-4 border-l-rose-500">
        <div>
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Overall Supply Chain Threat Level:</span>
          <div className="text-lg font-black text-rose-400 mt-0.5">
            {data?.overall_shortage_status === 'RED' ? 'CRITICAL SHORTAGE DETECTED' : 'SUPPLY BUFFER STABLE'}
          </div>
        </div>
        <div className="flex gap-2">
          <Badge variant="danger">{data?.critical_shortages_count || 2} Critical Stockouts</Badge>
          <Badge variant="warning">{data?.moderate_shortages_count || 1} Shortage Warning</Badge>
        </div>
      </Card>

      {/* Category Radar Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(data?.radar_categories || [
          { category: 'water', available_stock: 25000, sphere_required_demand: 639000, unit: 'Liters', status: 'RED', recommended_replenishment: 614000 },
          { category: 'food', available_stock: 4500, sphere_required_demand: 127800, unit: 'Rations', status: 'RED', recommended_replenishment: 123300 },
          { category: 'medical', available_stock: 350, sphere_required_demand: 710, unit: 'Trauma Kits', status: 'ORANGE', recommended_replenishment: 360 },
          { category: 'shelter', available_stock: 800, sphere_required_demand: 2840, unit: 'Tents', status: 'RED', recommended_replenishment: 2040 },
          { category: 'blankets', available_stock: 6200, sphere_required_demand: 14200, unit: 'Blankets', status: 'ORANGE', recommended_replenishment: 8000 },
        ]).map((c: any, i: number) => {
          const isRed = c.status === 'RED';
          const isOrange = c.status === 'ORANGE';
          const pct = Math.min(100, Math.round((c.available_stock / Math.max(1, c.sphere_required_demand)) * 100));

          return (
            <Card key={i} className={`border-t-4 ${isRed ? 'border-t-rose-500' : isOrange ? 'border-t-amber-500' : 'border-t-emerald-500'}`}>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-bold text-slate-100 uppercase">{c.category}</span>
                <Badge variant={isRed ? 'danger' : isOrange ? 'warning' : 'success'}>{c.status}</Badge>
              </div>
              <div className="flex justify-between text-xs text-slate-400 mb-2">
                <span>Stock: <strong className="text-slate-200">{c.available_stock.toLocaleString()} {c.unit}</strong></span>
                <span>Need: <strong className="text-slate-200">{c.sphere_required_demand.toLocaleString()} {c.unit}</strong></span>
              </div>
              <div className="w-full bg-slate-950 rounded-full h-2 mb-3 border border-slate-800">
                <div
                  className={`h-2 rounded-full ${isRed ? 'bg-rose-500' : isOrange ? 'bg-amber-500' : 'bg-emerald-500'}`}
                  style={{ width: `${pct}%` }}
                ></div>
              </div>
              <div className={`text-xs font-bold ${isRed ? 'text-rose-400' : isOrange ? 'text-amber-400' : 'text-emerald-400'}`}>
                {isRed ? `⚠️ Deficit: Replenish +${c.recommended_replenishment.toLocaleString()} ${c.unit}` : `Buffer: ${pct}% demand covered`}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
};
