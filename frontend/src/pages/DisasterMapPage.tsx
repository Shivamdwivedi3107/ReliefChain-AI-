import React, { useEffect } from 'react';
import { Card, Badge } from '../components/common';

export const DisasterMapPage: React.FC = () => {
  useEffect(() => {
    // Check if Leaflet is available on window or dynamically load
    if ((window as any).L) {
      const L = (window as any).L;
      const mapContainer = document.getElementById('leaflet-map-container');
      if (mapContainer && !mapContainer.hasChildNodes()) {
        const map = L.map('leaflet-map-container').setView([19.0760, 72.8777], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; OpenStreetMap contributors',
        }).addTo(map);

        // Add demo markers
        L.circle([19.0760, 72.8777], {
          color: '#f43f5e',
          fillColor: '#f43f5e',
          fillOpacity: 0.25,
          radius: 12000,
        }).addTo(map).bindPopup('<b>Monsoon Inundation Sector 4</b><br>Severity: 8.8/10');

        L.marker([19.0760, 72.8777]).addTo(map).bindPopup('🚨 <b>Incident Ground Zero</b>');
      }
    }
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-slate-100 flex items-center gap-2">
            <span>🗺️</span> Interactive Disaster Map
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time geospatial hazard perimeters, clustered relief requests, and verified safe shelters.
          </p>
        </div>
        <Badge variant="primary">GEOJSON MAP FEED</Badge>
      </div>

      <Card className="p-0 overflow-hidden">
        <div id="leaflet-map-container" className="w-full h-[520px] bg-slate-900">
          <div className="flex items-center justify-center h-full text-slate-400 text-xs">
            Interactive Disaster Map Feed Loading...
          </div>
        </div>
      </Card>
    </div>
  );
};
