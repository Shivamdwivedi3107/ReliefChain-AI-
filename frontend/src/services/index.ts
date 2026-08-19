import api from './api';
import {
  ReliefRequest,
  ReliefRequestCreatePayload,
  QuickTriageResult,
  Incident,
  SituationReport,
  ShortageRadarResponse,
  TransparencyJourneyResponse,
  CopilotQueryResponse,
  SystemHealthResponse,
  RecommendedMission,
} from '../types';

export const reliefService = {
  async getRequests(params?: { status?: string; priority?: string }): Promise<ReliefRequest[]> {
    return api.get<ReliefRequest[]>('/relief-requests', { params });
  },

  async createRequest(payload: ReliefRequestCreatePayload): Promise<ReliefRequest> {
    return api.post<ReliefRequest>('/relief-requests', payload);
  },

  async getRequestById(id: string): Promise<ReliefRequest> {
    return api.get<ReliefRequest>(`/relief-requests/${id}`);
  },

  async quickTriage(payload: {
    people_count: number;
    has_medical_emergency: boolean;
    disaster_type: string;
    supplies_needed: string[];
  }): Promise<QuickTriageResult> {
    return api.post<QuickTriageResult>('/dashboards/citizen/quick-triage', payload);
  },
};

export const incidentService = {
  async getIncidents(params?: { status?: string; disaster_type?: string }): Promise<Incident[]> {
    return api.get<Incident[]>('/incidents', { params });
  },

  async getIncidentById(id: string): Promise<Incident> {
    return api.get<Incident>(`/incidents/${id}`);
  },

  async transitionStatus(id: string, targetStatus: string, note?: string): Promise<Incident> {
    return api.post<Incident>(`/incidents/${id}/transition`, { target_status: targetStatus, note });
  },

  async getSituationReports(incidentId?: string): Promise<SituationReport[]> {
    return api.get<SituationReport[]>('/situation-reports', { params: { incident_id: incidentId } });
  },

  async submitSituationReport(payload: Partial<SituationReport>): Promise<SituationReport> {
    return api.post<SituationReport>('/situation-reports', payload);
  },

  async getImpactZone(id: string): Promise<any> {
    return api.get<any>(`/geo/incidents/${id}/impact-zone`);
  },

  async getMapFeed(params?: any): Promise<any> {
    return api.get<any>('/geo/map', { params });
  },
};

export const resourceService = {
  async getShortageRadar(horizonDays = 3): Promise<ShortageRadarResponse> {
    return api.get<ShortageRadarResponse>(`/resources/shortage-radar?horizon_days=${horizonDays}`);
  },

  async getInventory(): Promise<any[]> {
    return api.get<any[]>('/resources/inventory');
  },

  async getCatalog(): Promise<any[]> {
    return api.get<any[]>('/resources');
  },
};

export const copilotService = {
  async getSuggestedPrompts(): Promise<{ prompts: Array<{ id: string; title: string; category: string; prompt: string }> }> {
    return api.get<{ prompts: Array<{ id: string; title: string; category: string; prompt: string }> }>('/copilot/suggested-prompts');
  },

  async query(prompt: string, incidentId?: string): Promise<CopilotQueryResponse> {
    return api.post<CopilotQueryResponse>('/copilot/query', { prompt, incident_id: incidentId });
  },
};

export const dashboardService = {
  async getCitizenDashboard(): Promise<any> {
    return api.get<any>('/dashboards/citizen');
  },

  async getVolunteerDashboard(): Promise<any> {
    return api.get<any>('/dashboards/volunteer');
  },

  async getAdminDashboard(): Promise<any> {
    return api.get<any>('/dashboards/admin');
  },

  async getCommandCenterSummary(): Promise<any> {
    return api.get<any>('/command-center/summary');
  },

  async getSystemHealth(): Promise<SystemHealthResponse> {
    return api.get<SystemHealthResponse>('/health/system-summary');
  },

  async getTransparencyJourney(referenceId: string): Promise<TransparencyJourneyResponse> {
    return api.get<TransparencyJourneyResponse>(`/transparency/journey/${encodeURIComponent(referenceId)}`);
  },

  async getLatestJourneys(): Promise<any[]> {
    return api.get<any[]>('/transparency/latest-journeys');
  },

  async loadDemoScenario(scenarioKey: string): Promise<any> {
    return api.post<any>('/demo/scenarios/load', { scenario_key: scenarioKey });
  },
};

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listeners: Array<(event: any) => void> = [];
  private reconnectInterval = 3000;
  private url: string;

  constructor(url?: string) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = url || `${protocol}//${window.location.host}/ws`;
  }

  public connect() {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((listener) => listener(data));
        } catch (e) {
          console.warn('WS JSON parse error:', e);
        }
      };
      this.ws.onclose = () => {
        setTimeout(() => this.connect(), this.reconnectInterval);
      };
      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch (err) {
      console.warn('WS Connection failed:', err);
    }
  }

  public onMessage(callback: (event: any) => void) {
    this.listeners.push(callback);
  }

  public disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketClient();
