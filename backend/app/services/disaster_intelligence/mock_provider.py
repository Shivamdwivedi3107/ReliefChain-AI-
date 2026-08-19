from datetime import datetime, timezone, timedelta
from typing import List
from app.services.disaster_intelligence.base import DisasterProvider
from app.services.disaster_intelligence.normalization import NormalizedDisasterEvent


class MockDisasterProvider(DisasterProvider):
    """Deterministic local mock disaster provider with realistic multi-hazard demo events."""

    @property
    def provider_name(self) -> str:
        return "mock_provider"

    async def fetch_events(self) -> List[NormalizedDisasterEvent]:
        now = datetime.now(timezone.utc)
        
        events = [
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-EQ-2026-001",
                disaster_type="earthquake",
                severity=7.8,
                title="Magnitude 7.8 Rift Fault Earthquake",
                description="Severe tectonic seismic event detected along Eastern Rift Fault. Significant structural distress reported.",
                latitude=28.6139,
                longitude=77.2090,
                affected_radius_km=45.0,
                started_at=now - timedelta(hours=3),
                status="active",
                confidence_score=0.96,
                raw_metadata={
                    "magnitude": 7.8,
                    "depth_km": 10.5,
                    "aftershocks_expected": True,
                    "sensor_network": "GLOBAL_SEISMIC_MOCK_NET",
                },
            ),
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-FL-2026-002",
                disaster_type="flood",
                severity=8.2,
                title="Category 4 River Delta Overflow",
                description="Heavy precipitation exceeding 220mm triggering critical river basin breaching and widespread inundation.",
                latitude=19.0760,
                longitude=72.8777,
                affected_radius_km=30.0,
                started_at=now - timedelta(hours=6),
                status="active",
                confidence_score=0.92,
                raw_metadata={
                    "water_level_m": 4.8,
                    "rainfall_24h_mm": 240,
                    "evacuation_ordered": True,
                },
            ),
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-CY-2026-003",
                disaster_type="cyclone",
                severity=8.9,
                title="Tropical Super Cyclone Inundation",
                description="Category 5 tropical storm system generating sustained wind speeds of 195km/h and 3.5m storm surges.",
                latitude=13.0827,
                longitude=80.2707,
                affected_radius_km=75.0,
                started_at=now - timedelta(hours=12),
                status="active",
                confidence_score=0.95,
                raw_metadata={
                    "wind_speed_kmh": 195,
                    "pressure_hpa": 930,
                    "storm_surge_m": 3.5,
                },
            ),
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-WF-2026-004",
                disaster_type="wildfire",
                severity=6.5,
                title="Rapid Combustion Scrub Wildfire",
                description="High temperature and arid winds accelerating brush fire perimeter expansion towards residential periphery.",
                latitude=12.9716,
                longitude=77.5946,
                affected_radius_km=20.0,
                started_at=now - timedelta(hours=24),
                status="monitoring",
                confidence_score=0.88,
                raw_metadata={
                    "containment_pct": 35,
                    "air_quality_aqi": 340,
                },
            ),
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-LS-2026-005",
                disaster_type="landslide",
                severity=5.5,
                title="Highland Highway Slope Displacement",
                description="Saturated hillside debris flow blocking primary transit artery and severing supply routes.",
                latitude=31.1048,
                longitude=77.1734,
                affected_radius_km=10.0,
                started_at=now - timedelta(hours=18),
                status="active",
                confidence_score=0.90,
                raw_metadata={
                    "road_blocked": True,
                    "slope_angle_deg": 48,
                },
            ),
            NormalizedDisasterEvent(
                source="mock_provider",
                external_id="MOCK-HW-2026-006",
                disaster_type="heatwave",
                severity=4.5,
                title="Severe Thermal Heat Anomaly",
                description="Ambient daytime temperatures sustained above 46°C for 5 consecutive operational cycles.",
                latitude=26.9124,
                longitude=75.7873,
                affected_radius_km=60.0,
                started_at=now - timedelta(days=2),
                status="monitoring",
                confidence_score=0.91,
                raw_metadata={
                    "peak_temp_c": 47.2,
                    "heat_index_c": 52.0,
                },
            ),
        ]
        return events
