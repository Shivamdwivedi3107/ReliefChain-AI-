/**
 * ReliefChain AI - Frontend Runtime Configuration
 * Allows configuring API and WebSocket endpoints dynamically across environments (Dev, Staging, Production).
 */
window.RELIEFCHAIN_CONFIG = window.RELIEFCHAIN_CONFIG || {
  // Base API endpoint URL (Auto-detected from current origin if hosted together)
  API_BASE: (() => {
    const custom = localStorage.getItem('reliefchain_custom_api_base');
    if (custom) return custom;
    if (window.location.protocol.startsWith('http')) {
      return `${window.location.origin}/api/v1`;
    }
    return 'http://127.0.0.1:8000/api/v1';
  })(),

  // WebSocket endpoint URL
  WS_BASE: (() => {
    const customWs = localStorage.getItem('reliefchain_custom_ws_base');
    if (customWs) return customWs;
    if (window.location.protocol === 'https:') {
      return `wss://${window.location.host}/ws/notifications`;
    }
    if (window.location.protocol === 'http:') {
      return `ws://${window.location.host}/ws/notifications`;
    }
    return 'ws://127.0.0.1:8000/ws/notifications';
  })(),

  APP_VERSION: '2.0.0-phase7',
  APP_ENV: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? 'development' : 'production',
};
