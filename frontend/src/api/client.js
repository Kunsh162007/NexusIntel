const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`API ${res.status}: ${err}`)
  }
  return res.json()
}

export const api = {
  // Engine
  getStatus: () => request('/api/engine/status'),
  startEngine: () => request('/api/engine/start', { method: 'POST' }),
  stopEngine: () => request('/api/engine/stop', { method: 'POST' }),
  getInsights: (track, limit = 50) =>
    request(`/api/engine/insights${track ? `?track=${track}&limit=${limit}` : `?limit=${limit}`}`),
  getWatchlist: () => request('/api/engine/watchlist'),
  addWatchItem: (item) => request('/api/engine/watchlist', { method: 'POST', body: JSON.stringify(item) }),
  removeWatchItem: (id) => request(`/api/engine/watchlist/${id}`, { method: 'DELETE' }),
  runDemo: (scenario) =>
    request('/api/engine/demo', { method: 'POST', body: JSON.stringify({ scenario }) }),

  // GTM
  getGTMInsights: (limit) => request(`/api/gtm/insights?limit=${limit || 20}`),
  gtmSearch: (query, country) =>
    request('/api/gtm/search', { method: 'POST', body: JSON.stringify({ query, country }) }),
  analyzeCompetitor: (url) =>
    request(`/api/gtm/competitor-analyze?url=${encodeURIComponent(url)}`),
  getHiringSignals: (company) =>
    request(`/api/gtm/hiring-signals?company=${encodeURIComponent(company)}`),

  // Finance
  getFinanceInsights: (limit) => request(`/api/finance/insights?limit=${limit || 20}`),
  financeSearch: (query) =>
    request('/api/finance/search', { method: 'POST', body: JSON.stringify({ query }) }),
  getRegulatoryFilings: (company) =>
    request(`/api/finance/regulatory-filings${company ? `?company=${encodeURIComponent(company)}` : ''}`),
  getPricingAnomalies: (product) =>
    request(`/api/finance/pricing-anomalies?product_query=${encodeURIComponent(product)}`),
  getAltData: (query) =>
    request(`/api/finance/alt-data?query=${encodeURIComponent(query)}`),

  // Security
  getSecurityInsights: (limit) => request(`/api/security/insights?limit=${limit || 20}`),
  threatScan: (query) =>
    request(`/api/security/threat-scan?query=${encodeURIComponent(query)}`),
  credentialCheck: (domain) =>
    request(`/api/security/credential-check?domain=${encodeURIComponent(domain)}`),
  brandMonitor: (brand) =>
    request(`/api/security/brand-monitor?brand=${encodeURIComponent(brand)}`),
  getRegulatoryChanges: (region) =>
    request(`/api/security/regulatory-changes?region=${encodeURIComponent(region || 'global')}`),
  getCveFeed: (product) =>
    request(`/api/security/cve-feed${product ? `?product=${encodeURIComponent(product)}` : ''}`),

  // Voice
  sendVoiceCommand: (audioBase64, format = 'wav') =>
    request('/api/voice/command', {
      method: 'POST',
      body: JSON.stringify({ audio_base64: audioBase64, format }),
    }),
}

export const WS_URL = BASE.replace(/^http/, 'ws') + '/api/engine/ws'
