export type UserRole = 'citizen' | 'volunteer' | 'ngo' | 'admin' | 'donor';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  phone_number?: string;
  is_active: boolean;
  is_verified: boolean;
  organization_id?: string;
  skills?: string[];
  max_mission_capacity?: number;
  reliability_score?: number;
  current_latitude?: number;
  current_longitude?: number;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type PriorityLevel = 'Critical' | 'High' | 'Medium' | 'Low';
export type ReliefStatus = 'pending' | 'triaged' | 'assigned' | 'dispatched' | 'completed' | 'cancelled';

export interface ReliefRequest {
  id: string;
  citizen_id: string;
  disaster_id?: string;
  disaster_type: string;
  location_name: string;
  latitude: number;
  longitude: number;
  affected_people: number;
  required_resources: string[];
  urgency_description: string;
  image_reference?: string;
  priority: PriorityLevel;
  status: ReliefStatus;
  is_simulated: boolean;
  assigned_organization_id?: string;
  assigned_volunteer_id?: string;
  ai_predicted_priority?: PriorityLevel;
  ai_confidence?: number;
  ai_factors?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface ReliefRequestCreatePayload {
  disaster_type: string;
  people_count: number;
  latitude: number;
  longitude: number;
  description: string;
  medical_urgency?: string;
  vulnerable_individuals?: number;
  items_needed?: string[];
}

export interface QuickTriageResult {
  priority: PriorityLevel;
  score: number;
  confidence: number;
  reason: string;
  recommended_action: string;
}

export type IncidentStatus = 'DETECTED' | 'VERIFIED' | 'ACTIVE' | 'MONITORING' | 'CONTAINED' | 'RESOLVED' | 'CANCELLED';
export type EscalationLevel = 'LEVEL_1_NORMAL' | 'LEVEL_2_ELEVATED' | 'LEVEL_3_HIGH' | 'LEVEL_4_CRITICAL';

export interface Incident {
  id: string;
  title: string;
  disaster_type: string;
  severity: number;
  status: IncidentStatus;
  escalation_level: EscalationLevel;
  latitude: number;
  longitude: number;
  affected_radius_km: number;
  event_id?: string;
  organization_id?: string;
  description?: string;
  metadata_json?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface SituationReport {
  id: string;
  incident_id: string;
  author_id?: string;
  report_type: string;
  summary: string;
  people_affected: number;
  people_displaced: number;
  casualties_reported: number;
  infrastructure_damage_level: string;
  medical_need_level?: string;
  food_need_level?: string;
  water_need_level?: string;
  shelter_need_level?: string;
  created_at: string;
}

export interface RecommendedMission {
  mission_id: string;
  mission_title: string;
  disaster_type: string;
  distance_km: number;
  match_score: number;
  match_reasons: string[];
}

export interface VolunteerProfile {
  id: string;
  name: string;
  email: string;
  skills: string[];
  max_capacity: number;
  current_active_missions: number;
  reliability_score: number;
  completed_missions_count: number;
}

export interface RadarCategory {
  category: string;
  available_stock: number;
  sphere_required_demand: number;
  unit: string;
  status: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
  recommended_replenishment: number;
}

export interface ShortageRadarResponse {
  overall_shortage_status: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED';
  horizon_days: number;
  affected_population_estimate: number;
  critical_shortages_count: number;
  moderate_shortages_count: number;
  radar_categories: RadarCategory[];
}

export interface TransparencyStage {
  stage_name: string;
  completed: boolean;
  timestamp?: string;
  details: string;
  sha256_hash?: string;
}

export interface TransparencyJourneyResponse {
  reference_id: string;
  journey_status: string;
  category: string;
  stages: TransparencyStage[];
  verified_block_count: number;
}

export interface CopilotQueryResponse {
  category: string;
  answer_markdown: string;
  key_drivers: string[];
  actionable_recommendations: string[];
  confidence_score: number;
  sources_consulted: string[];
}

export interface SystemHealthResponse {
  status: string;
  uptime_score_pct: number;
  avg_latency_ms: number;
  ai_model_accuracy_pct: number;
  ledger_state: string;
  subsystems: Array<{
    name: string;
    status: string;
    engine: string;
    details: string;
  }>;
}
