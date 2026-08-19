const API_BASE = window.location.protocol.startsWith('http')
  ? `${window.location.origin}/api/v1`
  : 'http://127.0.0.1:8001/api/v1';

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
        const errorMsg = data.message || data.detail || `Request failed with status ${res.status}`;
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
    this.setSession(res.access_token, res.user);
    return res;
  }

  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getMe() {
    return this.request('/auth/me');
  }

  logout() {
    this.setSession(null, null);
  }

  // --- Relief Requests ---
  async getReliefRequests(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request(`/relief-requests?${query}`);
  }

  async createReliefRequest(data) {
    return this.request('/relief-requests', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReliefRequestById(id) {
    return this.request(`/relief-requests/${id}`);
  }

  async updateReliefRequest(id, data) {
    return this.request(`/relief-requests/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async assignReliefRequest(id, payload) {
    return this.request(`/relief-requests/${id}/assign`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async deleteReliefRequest(id) {
    return this.request(`/relief-requests/${id}`, {
      method: 'DELETE',
    });
  }

  // --- AI Prioritization DSS ---
  async predictPriority(payload) {
    return this.request('/ai/predict-priority', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // --- Resources & Inventory ---
  async getResources(category = null) {
    const q = category ? `?category=${category}` : '';
    return this.request(`/resources${q}`);
  }

  async createResource(data) {
    return this.request('/resources', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getInventory(orgId = null) {
    const q = orgId ? `?organization_id=${orgId}` : '';
    return this.request(`/resources/inventory/list${q}`);
  }

  async addInventory(payload) {
    return this.request('/resources/inventory', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getLowStockAlerts(threshold = 25.0) {
    return this.request(`/resources/alerts/low-stock?threshold=${threshold}`);
  }

  // --- Distributions & QR Proof-of-Delivery ---
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

  async generateQR(distributionId) {
    return this.request(`/qr/generate/${distributionId}`, {
      method: 'POST',
    });
  }

  async verifyQRToken(token) {
    return this.request(`/qr/verify/${token}`);
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

  // --- Analytics & Stats ---
  async getSummaryStats() {
    return this.request('/analytics/summary');
  }

  async getDisasterStats() {
    return this.request('/analytics/disasters');
  }

  async getResourceStats() {
    return this.request('/analytics/resources');
  }

  async getOrganizations() {
    return this.request('/organizations');
  }
}

const api = new ApiService();
