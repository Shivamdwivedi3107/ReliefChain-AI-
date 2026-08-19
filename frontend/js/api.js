/**
 * ReliefChain AI - Centralized Frontend API Service
 */
const API_BASE = (window.RELIEFCHAIN_CONFIG && window.RELIEFCHAIN_CONFIG.API_BASE)
  ? window.RELIEFCHAIN_CONFIG.API_BASE
  : (window.location.protocol.startsWith('http')
      ? `${window.location.origin}/api/v1`
      : 'http://127.0.0.1:8000/api/v1');

class ApiService {
  constructor() {
    this.baseUrl = API_BASE;
    this.token = localStorage.getItem('reliefchain_token') || null;
    this.user = JSON.parse(localStorage.getItem('reliefchain_user') || 'null');
  }

  setSession(token, user) {
    this.token = token;
    this.user = user;
    if (token) {
      localStorage.setItem('reliefchain_token', token);
      localStorage.setItem('reliefchain_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('reliefchain_token');
      localStorage.removeItem('reliefchain_user');
    }
  }

  getHeaders(customHeaders = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...customHeaders,
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      ...options,
      headers: this.getHeaders(options.headers),
    };

    try {
      const res = await fetch(url, config);
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const errorMsg =
          (data.error && data.error.message) ||
          data.message ||
          data.detail ||
          `Request failed with status ${res.status}`;
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  }

  // --- Auth APIs ---
  async login(email, password) {
    const res = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res.access_token) {
      this.token = res.access_token;
      const profile = await this.getCurrentUser();
      this.setSession(res.access_token, profile);
      return profile;
    }
    return res;
  }

  async register(data) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  logout() {
    this.setSession(null, null);
  }

  // --- Relief Requests & SOS ---
  async getReliefRequests(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/relief-requests?${q}`);
  }

  async getReliefRequestById(id) {
    return this.request(`/relief-requests/${id}`);
  }

  async createReliefRequest(data) {
    return this.request('/relief-requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async assignReliefRequest(id, data) {
    return this.request(`/relief-requests/${id}/assign`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async predictPriority(data) {
    return this.request('/ai/predict-priority', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // --- Missions Lifecycle ---
  async getMissions(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/missions?${q}`);
  }

  async getMissionById(id) {
    return this.request(`/missions/${id}`);
  }

  async updateMissionStatus(id, newStatus, note = '') {
    return this.request(`/missions/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ new_status: newStatus, note }),
    });
  }

  async getMissionHistory(id) {
    return this.request(`/missions/${id}/history`);
  }

  // --- Warehouse Inventory & Resources ---
  async getResources(category = null) {
    const q = category ? `?category=${encodeURIComponent(category)}` : '';
    return this.request(`/resources${q}`);
  }

  async getInventory(orgId = null) {
    const q = orgId ? `?organization_id=${orgId}` : '';
    return this.request(`/resources/inventory/list${q}`);
  }

  async addInventory(data) {
    return this.request('/resources/inventory', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getLowStockAlerts(threshold = 25.0) {
    return this.request(`/resources/alerts/low-stock?threshold=${threshold}`);
  }

  // --- Distributions & QR Verification ---
  async getDistributions(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/distributions?${q}`);
  }

  async createDistribution(data) {
    return this.request('/distributions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async generateQRCode(distributionId) {
    return this.request(`/qr/generate/${distributionId}`, {
      method: 'POST',
    });
  }

  async confirmQRDelivery(verificationToken, latitude = 0.0, longitude = 0.0) {
    return this.request('/qr/confirm', {
      method: 'POST',
      body: JSON.stringify({
        verification_token: verificationToken,
        latitude,
        longitude,
      }),
    });
  }

  // --- Notifications ---
  async getNotifications(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/notifications?${q}`);
  }

  async getUnreadNotificationCount() {
    return this.request('/notifications/unread-count');
  }

  async markNotificationRead(id) {
    return this.request(`/notifications/${id}/read`, {
      method: 'PATCH',
    });
  }

  async markAllNotificationsRead() {
    return this.request('/notifications/read-all', {
      method: 'PATCH',
    });
  }

  // --- Donations ---
  async getDonations(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/donations?${q}`);
  }

  async createDonation(data) {
    return this.request('/donations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // --- Transparency Ledger & Blockchain ---
  async getLedgerTransactions(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/ledger?${q}`);
  }

  async getLedgerTransactionById(id) {
    return this.request(`/ledger/${id}`);
  }

  async verifyLedgerRecord(recordHash) {
    return this.request('/blockchain/verify', {
      method: 'POST',
      body: JSON.stringify({ record_hash: recordHash }),
    });
  }

  async verifyLedgerChainIntegrity() {
    return this.request('/ledger/verify');
  }

  // --- Humanitarian Analytics ---
  async getAnalyticsOverview() {
    return this.request('/analytics/overview');
  }

  async getPriorityDistribution() {
    return this.request('/analytics/priority-distribution');
  }

  async getDisasterTypes() {
    return this.request('/analytics/disaster-types');
  }

  async getMissionPerformance() {
    return this.request('/analytics/mission-performance');
  }

  async getInventorySummary() {
    return this.request('/analytics/inventory-summary');
  }

  async getOrganizations() {
    return this.request('/organizations');
  }

  // --- Geographic Intelligence ---
  async getNearbyRequests(lat, lng, radiusKm = 15, status = null) {
    let url = `/geo/nearby-requests?latitude=${lat}&longitude=${lng}&radius_km=${radiusKm}`;
    if (status) url += `&status=${status}`;
    return this.request(url);
  }

  async getDisasterHotspots(maxRadiusKm = 25) {
    return this.request(`/geo/disaster-hotspots?max_cluster_radius_km=${maxRadiusKm}`);
  }

  // --- Smart Volunteer Recommendation ---
  async getRecommendedVolunteers(missionId, limit = 10) {
    return this.request(`/missions/${missionId}/recommended-volunteers?limit=${limit}`);
  }

  // --- AI Explainability & Model Info ---
  async getModelInfo() {
    return this.request('/ai/model-info');
  }

  async explainPriority(payload) {
    return this.request('/ai/explain-priority', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- Evidence Management ---
  async uploadEvidence(formData) {
    const headers = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const response = await fetch(`${this.baseUrl}/evidence/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || data.error?.message || 'Evidence upload failed');
    }
    return data;
  }

  async getEvidenceMetadata(evidenceId) {
    return this.request(`/evidence/${evidenceId}`);
  }

  async deleteEvidence(evidenceId) {
    return this.request(`/evidence/${evidenceId}`, { method: 'DELETE' });
  }

  // --- Notification Archive ---
  async archiveNotification(notificationId) {
    return this.request(`/notifications/${notificationId}/archive`, { method: 'POST' });
  }

  // --- Disaster Drill Simulation ---
  async startSimulation(scenario = 'cyclone_landing') {
    return this.request('/simulation/start', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    });
  }

  async stopSimulation(purgeData = true) {
    return this.request('/simulation/stop', {
      method: 'POST',
      body: JSON.stringify({ purge_data: purgeData }),
    });
  }

  async getSimulationStatus() {
    return this.request('/simulation/status');
  }

  // --- System Metrics & Telemetry ---
  async getMetricsSummary() {
    const headers = { Accept: 'application/json' };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
    const response = await fetch(`${this.baseUrl.replace('/api/v1', '')}/metrics`, { headers });
    return response.json();
  }

  // --- Phase 8: Advanced AI Intelligence & Disaster Risk ---
  async predictDisasterRisk(payload) {
    return this.request('/ai/risk-predict', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async forecastResourceDemand(payload) {
    return this.request('/ai/resource-forecast', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getVolunteerRecommendations(missionId, limit = 5) {
    return this.request(`/ai/volunteer-recommendations/${missionId}?limit=${limit}`);
  }

  async simulateDisasterImpact(payload) {
    return this.request('/ai/simulate-disaster', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getAIModels() {
    return this.request('/ai/models');
  }

  async getAIModelDetails(modelName) {
    return this.request(`/ai/models/${modelName}`);
  }

  async activateAIModel(modelName, isActive = true) {
    return this.request('/ai/models/activate', {
      method: 'POST',
      body: JSON.stringify({ model_name: modelName, is_active: isActive }),
    });
  }

  async reloadAIModel() {
    return this.request('/ai/reload-model', { method: 'POST' });
  }

  async getAIIntelligenceAnalytics() {
    return this.request('/analytics/ai-intelligence');
  }

  // --- Phase 9: Real-Time Disaster Intelligence & Incident Command ---
  async getCommandCenterSummary() {
    return this.request('/command-center/summary');
  }

  async getIncidents(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/incidents?${q}`);
  }

  async getIncident(id) {
    return this.request(`/incidents/${id}`);
  }

  async createIncident(data) {
    return this.request('/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async patchIncident(id, data) {
    return this.request(`/incidents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async verifyIncident(id, note = '') {
    return this.request(`/incidents/${id}/verify`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
  }

  async activateIncident(id, note = '') {
    return this.request(`/incidents/${id}/activate`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
  }

  async resolveIncident(id, note = '') {
    return this.request(`/incidents/${id}/resolve`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
  }

  async getIncidentTimeline(id) {
    return this.request(`/incidents/${id}/timeline`);
  }

  async getSituationReports(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/situation-reports?${q}`);
  }

  async submitSituationReport(data) {
    return this.request('/situation-reports', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async evaluateIncidentEscalation(id) {
    return this.request(`/incidents/${id}/evaluate-escalation`, {
      method: 'POST',
    });
  }

  async syncDisasterFeed(providerName = 'mock_provider') {
    return this.request(`/disaster-intelligence/sync?provider_name=${encodeURIComponent(providerName)}`, {
      method: 'POST',
    });
  }

  async getDisasterProviders() {
    return this.request('/disaster-intelligence/providers');
  }

  async getDisasterEvents(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/disaster-intelligence/events?${q}`);
  }

  async getNearbyIncidents(lat, lng, radiusKm = 50.0) {
    return this.request(`/geo/incidents/nearby?latitude=${lat}&longitude=${lng}&radius_km=${radiusKm}`);
  }

  async getIncidentImpactZone(id) {
    return this.request(`/geo/incidents/${id}/impact-zone`);
  }

  async getGeoJsonMapFeed(params = {}) {
    const q = new URLSearchParams(params).toString();
    return this.request(`/geo/map?${q}`);
  }

  // --- Phase 10 Extensions ---
  async getCopilotSuggestedPrompts() {
    return this.request('/copilot/suggested-prompts');
  }

  async queryCopilot(prompt, incidentId = null) {
    return this.request('/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ prompt, incident_id: incidentId }),
    });
  }

  async getShortageRadar(horizonDays = 3) {
    return this.request(`/resources/shortage-radar?horizon_days=${horizonDays}`);
  }

  async getTransparencyJourney(referenceId) {
    return this.request(`/transparency/journey/${encodeURIComponent(referenceId)}`);
  }

  async getLatestTransparencyJourneys() {
    return this.request('/transparency/latest-journeys');
  }

  async getDemoScenarios() {
    return this.request('/demo/scenarios');
  }

  async loadDemoScenario(scenarioKey) {
    return this.request('/demo/scenarios/load', {
      method: 'POST',
      body: JSON.stringify({ scenario_key: scenarioKey }),
    });
  }

  async getVolunteerDashboard() {
    return this.request('/dashboards/volunteer');
  }

  async getCitizenDashboard() {
    return this.request('/dashboards/citizen');
  }

  async getAdminDashboard() {
    return this.request('/dashboards/admin');
  }

  async quickCitizenTriage(data) {
    return this.request('/dashboards/citizen/quick-triage', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSystemHealthSummary() {
    return this.request('/health/system-summary');
  }
}

const api = new ApiService();



