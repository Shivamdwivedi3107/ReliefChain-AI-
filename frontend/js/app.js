/**
 * ReliefChain AI - Main Application Logic & Controller
 */

// Application State
const AppState = {
  activeTab: 'landing',
  user: null,
  requests: [],
  inventory: [],
  resources: [],
  distributions: [],
  ledger: [],
  organizations: [],
  stats: {},
};

// UI Notification Toasts
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Navigation & Tab Switching
function switchTab(tabId) {
  AppState.activeTab = tabId;
  document.querySelectorAll('.tab-content').forEach((tab) => {
    tab.classList.remove('active');
  });
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.classList.remove('active');
  });

  const activeContent = document.getElementById(`tab-${tabId}`);
  if (activeContent) activeContent.classList.add('active');

  const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (activeNav) activeNav.classList.add('active');

  // Trigger relevant data refreshes
  if (tabId === 'dashboard' || tabId === 'landing') loadDashboardStats();
  if (tabId === 'requests') loadReliefRequests();
  if (tabId === 'resources') loadInventory();
  if (tabId === 'distributions') loadDistributions();
  if (tabId === 'ledger') loadLedgerTransactions();
  if (tabId === 'analytics') loadAnalytics();
}

// Modal Handling
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// Auth State Updates
function updateAuthUI() {
  const user = api.user;
  AppState.user = user;
  const userProfileEl = document.getElementById('nav-user-profile');
  const authBtnEl = document.getElementById('nav-auth-btn');

  if (user) {
    if (authBtnEl) authBtnEl.style.display = 'none';
    if (userProfileEl) {
      userProfileEl.style.display = 'flex';
      userProfileEl.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: flex-end; font-size: 0.8rem;">
          <span style="font-weight: 600; color: var(--text-main);">${user.full_name || user.email}</span>
          <span class="badge badge-sm badge-status-assigned" style="font-size: 0.65rem; padding: 0.1rem 0.4rem;">${(user.role || 'user').toUpperCase()}</span>
        </div>
        <button class="btn btn-sm btn-outline" onclick="handleLogout()">Logout</button>
      `;
    }
  } else {
    if (authBtnEl) authBtnEl.style.display = 'inline-flex';
    if (userProfileEl) userProfileEl.style.display = 'none';
  }
}

async function handleLogout() {
  api.logout();
  updateAuthUI();
  showToast('Logged out successfully', 'info');
  switchTab('landing');
}

// Quick Demo Login
async function demoLogin(role) {
  const emailMap = {
    admin: 'admin@reliefchain.ai',
    volunteer: 'volunteer1@reliefchain.ai',
    ngo: 'ngo@reliefchain.ai',
    citizen: 'shivam@reliefchain.ai',
    donor: 'donor@reliefchain.ai',
  };
  const email = emailMap[role] || 'admin@reliefchain.ai';
  const password = 'SecurePassword123!';

  try {
    // Attempt login or register if not existing
    try {
      await api.login(email, password);
    } catch (e) {
      await api.register({
        email,
        full_name: `${role.toUpperCase()} Demo User`,
        password,
        role: role === 'ngo' ? 'ngo' : role,
      });
      await api.login(email, password);
    }
    updateAuthUI();
    closeModal('auth-modal');
    showToast(`Logged in as demo ${role.toUpperCase()}`, 'success');
    switchTab('dashboard');
  } catch (err) {
    showToast(`Demo login error: ${err.message}`, 'error');
  }
}

// Load Dashboard Overview KPIs
async function loadDashboardStats() {
  try {
    const [requestsRes, invRes, distRes, ledgerRes, donRes] = await Promise.all([
      api.getReliefRequests({ page: 1, page_size: 100 }).catch(() => ({ total: 0, data: [] })),
      api.getInventory().catch(() => []),
      api.getDistributions({ page: 1, page_size: 100 }).catch(() => ({ total: 0, data: [] })),
      api.getLedgerTransactions({ page: 1, page_size: 100 }).catch(() => ({ total: 0, data: [] })),
      api.getDonations({ page: 1, page_size: 100 }).catch(() => ({ total: 0, data: [] })),
    ]);

    const reqData = requestsRes.data || [];
    const criticalCount = reqData.filter((r) => r.priority === 'critical' && r.status !== 'completed').length;
    const totalDist = distRes.total || (distRes.data ? distRes.data.length : 0);
    const verifiedDist = (distRes.data || []).filter((d) => d.status === 'verified').length;
    const totalDonations = donRes.total || (donRes.data ? donRes.data.length : 0);

    // Update KPI elements
    const setVal = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };

    setVal('kpi-total-requests', requestsRes.total || reqData.length);
    setVal('kpi-critical-requests', criticalCount);
    setVal('kpi-inventory-items', invRes.length);
    setVal('kpi-distributions', `${verifiedDist}/${totalDist}`);
    setVal('kpi-ledger-blocks', ledgerRes.total || (ledgerRes.data ? ledgerRes.data.length : 0));
    setVal('kpi-donations', totalDonations);

    // Render Urgent Requests Triage Preview
    renderUrgentQueue(reqData.filter((r) => r.status !== 'completed').slice(0, 5));
  } catch (err) {
    console.error('Failed to load dashboard metrics:', err);
  }
}

function renderUrgentQueue(requests) {
  const container = document.getElementById('urgent-queue-table-body');
  if (!container) return;

  if (requests.length === 0) {
    container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 2rem;">No pending emergency requests in queue.</td></tr>`;
    return;
  }

  container.innerHTML = requests
    .map(
      (req) => `
    <tr>
      <td><strong>${req.location_name}</strong></td>
      <td>${req.disaster_type.toUpperCase()}</td>
      <td>${req.affected_people} Persons</td>
      <td><span class="badge badge-${req.priority}">${req.priority.toUpperCase()}</span></td>
      <td><span class="badge badge-status-${req.status}">${req.status.toUpperCase()}</span></td>
      <td>
        <button class="btn btn-sm btn-outline" onclick="openRequestDetails('${req.id}')">View Details</button>
      </td>
    </tr>
  `
    )
    .join('');
}

// Relief Requests List
async function loadReliefRequests() {
  const statusFilter = document.getElementById('request-status-filter')?.value || '';
  const priorityFilter = document.getElementById('request-priority-filter')?.value || '';
  const disasterFilter = document.getElementById('request-disaster-filter')?.value || '';
  const sortFilter = document.getElementById('request-sort-filter')?.value || 'urgency';

  const params = {
    page: 1,
    page_size: 50,
    sort_by: sortFilter,
  };
  if (statusFilter) params.status = statusFilter;
  if (priorityFilter) params.priority = priorityFilter;
  if (disasterFilter) params.disaster_type = disasterFilter;

  try {
    const res = await api.getReliefRequests(params);
    AppState.requests = res.data || [];
    renderReliefRequestsTable(AppState.requests);
  } catch (err) {
    showToast(`Error loading relief requests: ${err.message}`, 'error');
  }
}

function renderReliefRequestsTable(requests) {
  const container = document.getElementById('relief-requests-table-body');
  if (!container) return;

  if (!requests || requests.length === 0) {
    container.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 2.5rem;">No relief requests found matching criteria.</td></tr>`;
    return;
  }

  container.innerHTML = requests
    .map(
      (r) => `
    <tr>
      <td>
        <div style="font-weight: 600;">${r.location_name}</div>
        <div style="font-size: 0.75rem; color: var(--text-dim);">GPS: ${r.latitude.toFixed(3)}, ${r.longitude.toFixed(3)}</div>
      </td>
      <td><span class="badge" style="background: rgba(255,255,255,0.08);">${r.disaster_type}</span></td>
      <td>${r.affected_people}</td>
      <td>
        <span class="badge badge-${r.priority}">${r.priority}</span>
        ${r.ai_confidence ? `<div style="font-size: 0.7rem; color: var(--text-dim); margin-top: 2px;">AI: ${(r.ai_confidence * 100).toFixed(0)}% conf</div>` : ''}
      </td>
      <td><span class="badge badge-status-${r.status}">${r.status}</span></td>
      <td><span style="font-size: 0.8rem; color: var(--text-dim);">${new Date(r.created_at).toLocaleDateString()}</span></td>
      <td>
        <div style="display: flex; gap: 0.4rem;">
          <button class="btn btn-sm btn-outline" onclick="openRequestDetails('${r.id}')">Review</button>
          <button class="btn btn-sm btn-primary" onclick="initiateDispatchModal('${r.id}')">Dispatch</button>
        </div>
      </td>
    </tr>
  `
    )
    .join('');
}

// Request Details Modal
async function openRequestDetails(reqId) {
  try {
    const req = await api.getReliefRequestById(reqId);
    const body = document.getElementById('request-detail-body');
    if (!body) return;

    body.innerHTML = `
      <div style="margin-bottom: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h3 style="font-size: 1.2rem; font-weight: 700;">${req.location_name}</h3>
          <span class="badge badge-${req.priority}">${req.priority.toUpperCase()}</span>
        </div>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">Disaster: ${req.disaster_type} | Coordinates: ${req.latitude}, ${req.longitude}</p>
      </div>

      <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1rem;">
        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.5rem;">Urgency & Description</h4>
        <p style="font-size: 0.95rem; color: var(--text-main);">${req.urgency_description || 'No descriptive notes attached.'}</p>
      </div>

      <div style="background: rgba(6, 182, 212, 0.06); border: 1px solid rgba(6, 182, 212, 0.2); border-radius: var(--radius-md); padding: 1rem; margin-bottom: 1.25rem;">
        <h4 style="font-size: 0.85rem; text-transform: uppercase; color: var(--accent-cyan); margin-bottom: 0.5rem;">AI Prioritization Factors (DSS Triage)</h4>
        <div style="font-size: 0.85rem; color: var(--text-muted);">
          <div>• Predicted Priority: <strong>${(req.ai_predicted_priority || req.priority).toUpperCase()}</strong> (${((req.ai_confidence || 0.9) * 100).toFixed(0)}% confidence)</div>
          ${req.ai_factors ? `<pre style="font-size: 0.75rem; margin-top: 0.5rem; color: var(--text-dim); background: rgba(0,0,0,0.2); padding: 0.5rem; border-radius: 4px;">${JSON.stringify(req.ai_factors, null, 2)}</pre>` : ''}
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 1rem;">
        <button class="btn btn-sm btn-danger" onclick="handleDeleteRequest('${req.id}')">Delete Request</button>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-sm btn-outline" onclick="handleUpdateStatus('${req.id}', 'under_review')">Mark In Review</button>
          <button class="btn btn-sm btn-primary" onclick="initiateDispatchModal('${req.id}')">Dispatch Aid</button>
        </div>
      </div>
    `;

    openModal('request-detail-modal');
  } catch (err) {
    showToast(`Could not fetch details: ${err.message}`, 'error');
  }
}

async function handleUpdateStatus(reqId, newStatus) {
  try {
    await api.updateReliefRequest(reqId, { status: newStatus });
    showToast(`Request marked as ${newStatus}`, 'success');
    closeModal('request-detail-modal');
    loadReliefRequests();
  } catch (err) {
    showToast(`Failed updating status: ${err.message}`, 'error');
  }
}

async function handleDeleteRequest(reqId) {
  if (!confirm('Are you sure you want to cancel and delete this relief request?')) return;
  try {
    await api.deleteReliefRequest(reqId);
    showToast('Relief request deleted successfully', 'success');
    closeModal('request-detail-modal');
    loadReliefRequests();
  } catch (err) {
    showToast(`Deletion failed: ${err.message}`, 'error');
  }
}

// Live AI Triage Simulator for SOS Form
async function runLiveAiTriage() {
  const disasterType = document.getElementById('sos-disaster-type')?.value || 'flood';
  const affectedPeople = parseInt(document.getElementById('sos-affected-people')?.value || '1', 10);
  const medicalNeeded = document.getElementById('sos-need-medical')?.checked ? 1 : 0;
  const waterNeeded = document.getElementById('sos-need-water')?.checked ? 1 : 0;
  const foodNeeded = document.getElementById('sos-need-food')?.checked ? 1 : 0;
  const vulnerableNeeded = document.getElementById('sos-need-vulnerable')?.checked ? 1 : 0;

  try {
    const res = await api.predictPriority({
      disaster_type: disasterType,
      affected_people: affectedPeople,
      medical_needed: medicalNeeded,
      water_needed: waterNeeded,
      food_needed: foodNeeded,
      vulnerable_population: vulnerableNeeded,
      location_risk_score: 5.0,
    });

    const badgeEl = document.getElementById('sos-ai-priority-badge');
    const scoreEl = document.getElementById('sos-ai-score-display');
    if (badgeEl && scoreEl) {
      badgeEl.className = `badge badge-${res.predicted_priority}`;
      badgeEl.textContent = res.priority_level.toUpperCase();
      scoreEl.textContent = `Priority Score: ${res.priority_score}/100`;
    }
  } catch (err) {
    console.error('Live AI simulation failed:', err);
  }
}

// Submit SOS Request Form
async function handleSosSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const disasterType = document.getElementById('sos-disaster-type').value;
  const locationName = document.getElementById('sos-location-name').value;
  const affectedPeople = parseInt(document.getElementById('sos-affected-people').value || '1', 10);
  const lat = parseFloat(document.getElementById('sos-lat').value || '28.6139');
  const lng = parseFloat(document.getElementById('sos-lng').value || '77.2090');
  const description = document.getElementById('sos-description').value;

  const requiredResources = [];
  if (document.getElementById('sos-need-medical').checked) requiredResources.push({ item: 'trauma medical kit', qty: 2 });
  if (document.getElementById('sos-need-water').checked) requiredResources.push({ item: 'potable water bottles', qty: 20 });
  if (document.getElementById('sos-need-food').checked) requiredResources.push({ item: 'emergency food rations', qty: 20 });
  if (document.getElementById('sos-need-vulnerable').checked) requiredResources.push({ item: 'infant/elderly care supplies', qty: 5 });

  try {
    // If not logged in, auto-authenticate demo citizen
    if (!api.token) {
      await demoLogin('citizen');
    }

    const payload = {
      disaster_type: disasterType,
      location_name: locationName,
      affected_people: affectedPeople,
      latitude: lat,
      longitude: lng,
      required_resources: requiredResources,
      urgency_description: description,
    };

    const res = await api.createReliefRequest(payload);
    showToast(`SOS Emergency Request registered! Priority: ${res.priority.toUpperCase()}`, 'success');
    form.reset();
    closeModal('sos-modal');
    switchTab('requests');
  } catch (err) {
    showToast(`SOS Submission failed: ${err.message}`, 'error');
  }
}

// Resources & Inventory View
async function loadInventory() {
  try {
    const [resourcesRes, inventoryRes, alertsRes] = await Promise.all([
      api.getResources(),
      api.getInventory(),
      api.getLowStockAlerts(30.0).catch(() => []),
    ]);

    AppState.resources = resourcesRes || [];
    AppState.inventory = inventoryRes || [];

    renderInventoryTable(AppState.inventory);
    renderLowStockAlerts(alertsRes || []);
  } catch (err) {
    showToast(`Inventory load failed: ${err.message}`, 'error');
  }
}

function renderInventoryTable(inventory) {
  const container = document.getElementById('inventory-table-body');
  if (!container) return;

  if (!inventory || inventory.length === 0) {
    container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 2.5rem;">No warehouse inventory registered yet.</td></tr>`;
    return;
  }

  container.innerHTML = inventory
    .map((inv) => {
      const isLow = inv.available_quantity < 20;
      return `
      <tr>
        <td><strong>${inv.resource?.name || 'Resource Item'}</strong></td>
        <td><span class="badge" style="background: rgba(255,255,255,0.06);">${inv.resource?.category || 'General'}</span></td>
        <td><span style="font-weight: 700; color: ${isLow ? 'var(--accent-rose)' : 'var(--accent-emerald)'};">${inv.available_quantity} ${inv.resource?.unit || 'units'}</span></td>
        <td>${inv.reserved_quantity}</td>
        <td>${inv.total_quantity}</td>
        <td><span style="color: var(--text-dim); font-size: 0.85rem;">${inv.warehouse_location || 'Main Depot'}</span></td>
      </tr>
    `;
    })
    .join('');
}

function renderLowStockAlerts(alerts) {
  const container = document.getElementById('inventory-alerts-container');
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = `<div style="color: var(--accent-emerald); font-size: 0.85rem; padding: 0.5rem 0;">✓ All supplies above safe replenishment threshold.</div>`;
    return;
  }

  container.innerHTML = alerts
    .map(
      (a) => `
    <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: var(--radius-sm); padding: 0.6rem 1rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <span style="color: var(--accent-rose); font-weight: 700;">⚠ Low Stock Alert:</span>
        <span style="color: var(--text-main); margin-left: 0.5rem;">${a.resource?.name || 'Item'} (${a.available_quantity} remaining)</span>
      </div>
      <button class="btn btn-sm btn-outline" onclick="openModal('add-stock-modal')">Restock</button>
    </div>
  `
    )
    .join('');
}

// Add Inventory Stock Form
async function handleAddInventory(e) {
  e.preventDefault();
  const resourceId = document.getElementById('stock-resource-select').value;
  const quantity = parseFloat(document.getElementById('stock-quantity').value || '10');
  const warehouse = document.getElementById('stock-warehouse').value;

  try {
    if (!api.token) await demoLogin('ngo');
    await api.addInventory({
      resource_id: resourceId,
      quantity,
      warehouse_location: warehouse,
    });
    showToast('Warehouse inventory updated successfully', 'success');
    closeModal('add-stock-modal');
    loadInventory();
  } catch (err) {
    showToast(`Failed adding stock: ${err.message}`, 'error');
  }
}

// Distributions & QR Verification
async function loadDistributions() {
  try {
    const res = await api.getDistributions({ page: 1, page_size: 50 });
    AppState.distributions = res.data || [];
    renderDistributionsTable(AppState.distributions);
  } catch (err) {
    showToast(`Error loading distributions: ${err.message}`, 'error');
  }
}

function renderDistributionsTable(distributions) {
  const container = document.getElementById('distributions-table-body');
  if (!container) return;

  if (!distributions || distributions.length === 0) {
    container.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 2.5rem;">No active distribution missions dispatched.</td></tr>`;
    return;
  }

  container.innerHTML = distributions
    .map(
      (d) => `
    <tr>
      <td><strong>${d.relief_request?.location_name || 'Relief Target'}</strong></td>
      <td>${d.resource?.name || 'Supply Item'}</td>
      <td>${d.quantity} ${d.resource?.unit || ''}</td>
      <td><span class="badge badge-status-${d.status}">${d.status.toUpperCase()}</span></td>
      <td><span class="hash-pill" onclick="copyToClipboard('${d.qr_token}')" title="Click to copy QR Token">${d.qr_token ? d.qr_token.substring(0, 10) + '...' : 'N/A'}</span></td>
      <td><span class="hash-pill" onclick="openLedgerDetail('${d.id}')">${d.blockchain_tx_hash ? d.blockchain_tx_hash.substring(0, 10) + '...' : 'Pending Ledger'}</span></td>
      <td>
        <button class="btn btn-sm btn-outline" onclick="viewDistributionQR('${d.id}')">View QR</button>
      </td>
    </tr>
  `
    )
    .join('');
}

// Show QR Code modal for a distribution
async function viewDistributionQR(distId) {
  try {
    const res = await api.generateQR(distId);
    const container = document.getElementById('qr-modal-body');
    if (!container) return;

    container.innerHTML = `
      <div style="text-align: center;">
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">Present this tamper-evident QR code to the authorized field volunteer upon handover.</p>
        <div class="qr-box">
          <img src="${res.qr_code_image_base64}" alt="Distribution Verification QR Code" />
        </div>
        <div style="margin-top: 1rem;">
          <div style="font-size: 0.8rem; color: var(--text-dim); margin-bottom: 0.25rem;">Cryptographic Verification Token:</div>
          <span class="hash-pill" style="font-size: 0.9rem; word-break: break-all;">${res.verification_token}</span>
        </div>
        <div style="margin-top: 1.5rem;">
          <button class="btn btn-primary" onclick="simulateVolunteerScan('${res.verification_token}')">Simulate Field Volunteer Scan</button>
        </div>
      </div>
    `;

    openModal('qr-modal');
  } catch (err) {
    showToast(`Failed loading QR code: ${err.message}`, 'error');
  }
}

// Volunteer QR Handover Scanner Simulator
async function simulateVolunteerScan(token) {
  closeModal('qr-modal');
  const tokenInput = document.getElementById('scan-token-input');
  if (tokenInput) tokenInput.value = token;
  openModal('volunteer-scan-modal');
}

async function handleConfirmDelivery(e) {
  e.preventDefault();
  const token = document.getElementById('scan-token-input').value.trim();
  const lat = parseFloat(document.getElementById('scan-lat').value || '28.5355');
  const lng = parseFloat(document.getElementById('scan-lng').value || '77.3910');

  try {
    if (!api.token) await demoLogin('volunteer');
    const res = await api.confirmQRDelivery(token, lat, lng);
    showToast(`✓ Delivery Verified & Committed to Blockchain Ledger! (Tx: ${res.blockchain_tx_hash.substring(0, 10)}...)`, 'success');
    closeModal('volunteer-scan-modal');
    loadDistributions();
    loadDashboardStats();
  } catch (err) {
    showToast(`Verification failed: ${err.message}`, 'error');
  }
}

// Dispatch Aid Modal Initiator
async function initiateDispatchModal(reqId) {
  closeModal('request-detail-modal');
  const req = AppState.requests.find((r) => r.id === reqId);
  const selectReq = document.getElementById('dispatch-req-id');
  if (selectReq) selectReq.value = reqId;

  // Populate Resource picker
  const resSelect = document.getElementById('dispatch-resource-select');
  if (resSelect) {
    const resources = await api.getResources().catch(() => []);
    resSelect.innerHTML = resources.map((r) => `<option value="${r.id}">${r.name} (${r.category})</option>`).join('');
  }

  // Populate Organization picker
  const orgSelect = document.getElementById('dispatch-org-select');
  if (orgSelect) {
    const orgs = await api.getOrganizations().catch(() => []);
    orgSelect.innerHTML = orgs.map((o) => `<option value="${o.id}">${o.name}</option>`).join('');
  }

  openModal('dispatch-modal');
}

async function handleCreateDistribution(e) {
  e.preventDefault();
  const reqId = document.getElementById('dispatch-req-id').value;
  const resId = document.getElementById('dispatch-resource-select').value;
  const orgId = document.getElementById('dispatch-org-select').value;
  const qty = parseFloat(document.getElementById('dispatch-qty').value || '5');
  const location = document.getElementById('dispatch-depot').value;

  try {
    if (!api.token) await demoLogin('admin');
    await api.createDistribution({
      relief_request_id: reqId,
      resource_id: resId,
      organization_id: orgId,
      quantity: qty,
      dispatch_location: location,
    });
    showToast('Distribution dispatched successfully & inventory locked', 'success');
    closeModal('dispatch-modal');
    switchTab('distributions');
  } catch (err) {
    showToast(`Dispatch failed: ${err.message}`, 'error');
  }
}

// Transparency Ledger Explorer
async function loadLedgerTransactions() {
  try {
    const res = await api.getLedgerTransactions({ page: 1, page_size: 50 });
    AppState.ledger = res.data || [];
    renderLedgerTable(AppState.ledger);
  } catch (err) {
    showToast(`Error loading ledger: ${err.message}`, 'error');
  }
}

function renderLedgerTable(transactions) {
  const container = document.getElementById('ledger-table-body');
  if (!container) return;

  if (!transactions || transactions.length === 0) {
    container.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 2.5rem;">No blockchain audit records found.</td></tr>`;
    return;
  }

  container.innerHTML = transactions
    .map(
      (tx) => `
    <tr>
      <td><span style="font-weight: 700; color: var(--accent-cyan);">#${tx.block_number || 100}</span></td>
      <td><span class="badge" style="background: rgba(6, 182, 212, 0.15); color: var(--accent-cyan);">${tx.event_type.toUpperCase()}</span></td>
      <td><span class="hash-pill" onclick="copyToClipboard('${tx.tx_hash}')" title="Click to copy Transaction Hash">${tx.tx_hash ? tx.tx_hash.substring(0, 14) + '...' : '0x00...'}</span></td>
      <td><span class="hash-pill" onclick="copyToClipboard('${tx.previous_hash}')" title="Previous Block Hash">${tx.previous_hash ? tx.previous_hash.substring(0, 10) + '...' : '0x00...'}</span></td>
      <td><span class="badge badge-status-${tx.status}">${tx.status.toUpperCase()}</span></td>
      <td><span style="font-size: 0.8rem; color: var(--text-dim);">${new Date(tx.created_at).toLocaleTimeString()}</span></td>
    </tr>
  `
    )
    .join('');
}

// 1-Click Cryptographic Chain Integrity Verification
async function runLedgerVerification() {
  const resultBox = document.getElementById('ledger-verification-result');
  if (resultBox) {
    resultBox.innerHTML = `<span style="color: var(--accent-cyan);">Running SHA-256 Merkle chain verification across all blocks...</span>`;
  }

  try {
    const res = await api.verifyLedgerChainIntegrity();
    if (resultBox) {
      if (res.is_valid) {
        resultBox.innerHTML = `
          <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid var(--accent-emerald); border-radius: var(--radius-md); padding: 1rem; color: var(--accent-emerald); font-weight: 600;">
            ✓ Chain Integrity Verified: ${res.verified_blocks}/${res.total_blocks} Blocks Validated. Tamper-evident guarantee cryptographically sealed.
          </div>
        `;
      } else {
        resultBox.innerHTML = `
          <div style="background: rgba(244, 63, 94, 0.15); border: 1px solid var(--accent-rose); border-radius: var(--radius-md); padding: 1rem; color: var(--accent-rose); font-weight: 600;">
            ✕ Verification Alert: Found ${res.broken_links.length} compromised or corrupted blocks.
          </div>
        `;
      }
    }
  } catch (err) {
    showToast(`Verification request failed: ${err.message}`, 'error');
  }
}

// Analytics Visualizer (SVG Dynamic Charts)
async function loadAnalytics() {
  try {
    const [requestsRes, resourcesRes, statsRes] = await Promise.all([
      api.getReliefRequests({ page: 1, page_size: 100 }).catch(() => ({ data: [] })),
      api.getResources().catch(() => []),
      api.getSummaryStats().catch(() => ({})),
    ]);

    const reqs = requestsRes.data || [];
    renderDisasterTypeChart(reqs);
    renderPriorityDonutChart(reqs);
    renderStatusDistributionChart(reqs);
  } catch (err) {
    console.error('Analytics load error:', err);
  }
}

function renderDisasterTypeChart(requests) {
  const container = document.getElementById('chart-disasters');
  if (!container) return;

  const counts = { flood: 0, earthquake: 0, cyclone: 0, wildfire: 0, landslide: 0, other: 0 };
  requests.forEach((r) => {
    const type = r.disaster_type?.toLowerCase() || 'other';
    counts[type] = (counts[type] || 0) + 1;
  });

  const maxVal = Math.max(...Object.values(counts), 1);
  const bars = Object.entries(counts)
    .map(([type, val]) => {
      const heightPct = Math.max((val / maxVal) * 100, 10);
      return `
      <div style="display: flex; flex-direction: column; align-items: center; gap: 0.5rem; flex: 1;">
        <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-main);">${val}</div>
        <div style="width: 100%; height: 160px; display: flex; align-items: flex-end; justify-content: center; background: rgba(255,255,255,0.02); border-radius: 6px;">
          <div style="width: 60%; height: ${heightPct}%; background: linear-gradient(180deg, var(--accent-cyan), var(--accent-blue)); border-radius: 4px; transition: height 0.5s ease;"></div>
        </div>
        <div style="font-size: 0.75rem; color: var(--text-dim); text-transform: uppercase;">${type}</div>
      </div>
    `;
    })
    .join('');

  container.innerHTML = `<div style="display: flex; gap: 1rem; width: 100%; height: 100%; align-items: flex-end;">${bars}</div>`;
}

function renderPriorityDonutChart(requests) {
  const container = document.getElementById('chart-priority');
  if (!container) return;

  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  requests.forEach((r) => {
    const p = r.priority?.toLowerCase() || 'medium';
    counts[p] = (counts[p] || 0) + 1;
  });

  const total = requests.length || 1;
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 0.75rem; width: 100%;">
      ${Object.entries(counts)
        .map(([level, count]) => {
          const pct = ((count / total) * 100).toFixed(0);
          const colorMap = { critical: 'var(--accent-rose)', high: 'var(--accent-amber)', medium: 'var(--accent-blue)', low: 'var(--accent-emerald)' };
          return `
          <div>
            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 0.25rem;">
              <span style="text-transform: uppercase; font-weight: 600; color: ${colorMap[level]}">${level}</span>
              <span style="color: var(--text-muted);">${count} requests (${pct}%)</span>
            </div>
            <div style="height: 8px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden;">
              <div style="height: 100%; width: ${pct}%; background: ${colorMap[level]}; border-radius: 999px;"></div>
            </div>
          </div>
        `;
        })
        .join('')}
    </div>
  `;
}

function renderStatusDistributionChart(requests) {
  const container = document.getElementById('chart-status');
  if (!container) return;

  const counts = { pending: 0, assigned: 0, in_progress: 0, completed: 0 };
  requests.forEach((r) => {
    const s = r.status?.toLowerCase() || 'pending';
    if (counts[s] !== undefined) counts[s]++;
  });

  container.innerHTML = `
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; width: 100%;">
      <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: var(--radius-md); padding: 1rem; text-align: center;">
        <div style="font-size: 1.75rem; font-weight: 800; color: var(--accent-amber);">${counts.pending}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Pending Triage</div>
      </div>
      <div style="background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.25); border-radius: var(--radius-md); padding: 1rem; text-align: center;">
        <div style="font-size: 1.75rem; font-weight: 800; color: var(--accent-purple);">${counts.assigned}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Assigned Missions</div>
      </div>
      <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: var(--radius-md); padding: 1rem; text-align: center;">
        <div style="font-size: 1.75rem; font-weight: 800; color: var(--accent-cyan);">${counts.in_progress}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">In Transit</div>
      </div>
      <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-md); padding: 1rem; text-align: center;">
        <div style="font-size: 1.75rem; font-weight: 800; color: var(--accent-emerald);">${counts.completed}</div>
        <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Delivered & Verified</div>
      </div>
    </div>
  `;
}

// Donation Intake Handler
async function handleDonationSubmit(e) {
  e.preventDefault();
  const donorName = document.getElementById('don-name').value;
  const donorEmail = document.getElementById('don-email').value;
  const donType = document.getElementById('don-type').value;
  const amount = parseFloat(document.getElementById('don-amount').value || '100');
  const orgId = document.getElementById('don-org-select').value;
  const notes = document.getElementById('don-notes').value;

  try {
    const payload = {
      donor_name: donorName,
      donor_email: donorEmail,
      donation_type: donType,
      amount: donType === 'monetary' ? amount : null,
      currency: 'USD',
      organization_id: orgId,
      notes,
    };

    const res = await api.createDonation(payload);
    showToast(`Donation registered & sealed to blockchain! (Tx: ${res.blockchain_tx_hash ? res.blockchain_tx_hash.substring(0, 10) : '0x..'})`, 'success');
    closeModal('donate-modal');
    loadDashboardStats();
  } catch (err) {
    showToast(`Donation error: ${err.message}`, 'error');
  }
}

// Copy to Clipboard Utility
function copyToClipboard(text) {
  if (!text) return;
  navigator.clipboard.writeText(text);
  showToast('Copied to clipboard!', 'info');
}

// Initialization on DOM load
document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  switchTab('landing');

  // Populate Resource & Organization drop-downs in modals
  api.getResources().then((resources) => {
    const select = document.getElementById('stock-resource-select');
    if (select && resources) {
      select.innerHTML = resources.map((r) => `<option value="${r.id}">${r.name} (${r.category})</option>`).join('');
    }
  });

  api.getOrganizations().then((orgs) => {
    const donSelect = document.getElementById('don-org-select');
    if (donSelect && orgs) {
      donSelect.innerHTML = orgs.map((o) => `<option value="${o.id}">${o.name}</option>`).join('');
    }
  });

  // Attach SOS live prediction change listeners
  ['sos-disaster-type', 'sos-affected-people', 'sos-need-medical', 'sos-need-water', 'sos-need-food', 'sos-need-vulnerable'].forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('change', runLiveAiTriage);
      el.addEventListener('input', runLiveAiTriage);
    }
  });
});
