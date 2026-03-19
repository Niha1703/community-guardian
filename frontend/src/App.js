import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const API = '';

// ─── Severity Config ──────────────────────────────────────────────────────────
const SEVERITY = {
  critical: { color: '#ff2d55', bg: 'rgba(255,45,85,0.12)', label: 'CRITICAL', icon: '🔴' },
  high:     { color: '#ff9f0a', bg: 'rgba(255,159,10,0.12)', label: 'HIGH',     icon: '🟠' },
  medium:   { color: '#ffd60a', bg: 'rgba(255,214,10,0.12)', label: 'MEDIUM',   icon: '🟡' },
  low:      { color: '#30d158', bg: 'rgba(48,209,88,0.12)',  label: 'LOW',      icon: '🟢' },
  none:     { color: '#636366', bg: 'rgba(99,99,102,0.12)',  label: 'INFO',     icon: '⚪' },
};

const MOOD_CONFIG = {
  calm:   { color: '#30d158', text: 'All Clear', icon: '🛡️' },
  alert:  { color: '#ffd60a', text: 'Stay Informed', icon: '⚠️' },
  urgent: { color: '#ff2d55', text: 'Take Action', icon: '🚨' },
};

// ─── API Calls ────────────────────────────────────────────────────────────────
async function fetchAlerts(filters = {}) {
  const params = new URLSearchParams({ hide_noise: true, ...filters });
  const res = await fetch(`${API}/api/alerts/?${params}`);
  if (!res.ok) throw new Error('Failed to fetch alerts');
  return res.json();
}

async function fetchDigest(location) {
  const res = await fetch(`${API}/api/digest/?location=${encodeURIComponent(location)}`);
  if (!res.ok) throw new Error('Failed to fetch digest');
  return res.json();
}

async function createAlert(data) {
  const res = await fetch(`${API}/api/alerts/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.detail?.[0]?.msg || json.detail || 'Failed to submit alert');
  return json;
}

async function generateChecklist(threat_type, threat_description) {
  const res = await fetch(`${API}/api/checklist/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ threat_type, threat_description }),
  });
  if (!res.ok) throw new Error('Failed to generate checklist');
  return res.json();
}

async function updateAlert(id, data) {
  const res = await fetch(`${API}/api/alerts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to update alert');
  return res.json();
}

// ─── Components ───────────────────────────────────────────────────────────────

function DigestBanner({ location }) {
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDigest(location)
      .then(setDigest)
      .catch(() => setDigest(null))
      .finally(() => setLoading(false));
  }, [location]);

  if (loading) return <div className="digest-banner loading"><div className="pulse">Analyzing your area...</div></div>;
  if (!digest) return null;

  const mood = MOOD_CONFIG[digest.mood] || MOOD_CONFIG.calm;

  return (
    <div className="digest-banner" style={{ borderColor: mood.color }}>
      <div className="digest-left">
        <span className="digest-icon">{mood.icon}</span>
        <div>
          <div className="digest-status" style={{ color: mood.color }}>{mood.text.toUpperCase()}</div>
          <div className="digest-headline">{digest.headline}</div>
          <div className="digest-summary">{digest.summary}</div>
        </div>
      </div>
      <div className="digest-right">
        <div className="digest-count">{digest.alert_count}</div>
        <div className="digest-count-label">active alerts</div>
        {digest.ai_powered && <div className="ai-badge">⚡ AI Analysis</div>}
        {!digest.ai_powered && <div className="ai-badge fallback">📋 Rule-based</div>}
      </div>
    </div>
  );
}

function AlertCard({ alert, onChecklist, onVerify }) {
  const sev = SEVERITY[alert.severity] || SEVERITY.low;
  const time = new Date(alert.timestamp).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });

  return (
    <div className="alert-card" style={{ borderLeftColor: sev.color }}>
      <div className="alert-header">
        <div className="alert-meta">
          <span className="sev-badge" style={{ color: sev.color, background: sev.bg }}>
            {sev.icon} {sev.label}
          </span>
          {alert.verified && <span className="verified-badge">✓ VERIFIED</span>}
          {alert.ai_powered && <span className="ai-mini">⚡ AI</span>}
        </div>
        <div className="alert-time">{time}</div>
      </div>

      <div className="alert-location">📍 {alert.location}</div>

      {alert.ai_summary ? (
        <div className="alert-summary">{alert.ai_summary}</div>
      ) : (
        <div className="alert-raw">{alert.raw_text}</div>
      )}

      {alert.action_step && (
        <div className="alert-action">
          <span className="action-icon">→</span> {alert.action_step}
        </div>
      )}

      <div className="alert-footer">
        <span className="alert-source">{alert.source.replace(/_/g, ' ')}</span>
        <div className="alert-actions">
          {!alert.verified && (
            <button className="btn-ghost" onClick={() => onVerify(alert.id)}>
              Mark Verified
            </button>
          )}
          <button
            className="btn-primary-sm"
            onClick={() => onChecklist(alert.category, alert.raw_text)}
          >
            Get Checklist
          </button>
        </div>
      </div>
    </div>
  );
}

function ChecklistModal({ checklist, onClose }) {
  if (!checklist) return null;
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{checklist.title}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-meta">
          <span>⏱ {checklist.estimated_time}</span>
          <span>📊 {checklist.difficulty}</span>
          {checklist.ai_powered ? <span className="ai-badge">⚡ AI Generated</span> : <span className="ai-badge fallback">📋 Rule-based</span>}
        </div>
        <ol className="checklist">
          {checklist.steps.map((step, i) => (
            <li key={i} className="checklist-item">
              <span className="step-num">{i + 1}</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
        <button className="btn-primary" onClick={onClose}>Got it, I'm on it →</button>
      </div>
    </div>
  );
}

function ReportForm({ onSubmit, onClose }) {
  const [form, setForm] = useState({ raw_text: '', location: '', category: 'general', source: 'community_report' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError('');
    if (!form.raw_text.trim() || form.raw_text.trim().length < 10) {
      setError('Please describe the incident in at least 10 characters.');
      return;
    }
    if (!form.location.trim()) {
      setError('Location is required.');
      return;
    }
    setLoading(true);
    try {
      await onSubmit(form);
      onClose();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Report an Incident</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="form-group">
          <label>What happened? *</label>
          <textarea
            placeholder="Describe the incident clearly... (min 10 characters)"
            value={form.raw_text}
            onChange={e => setForm({ ...form, raw_text: e.target.value })}
            rows={4}
          />
          <div className="char-count">{form.raw_text.length}/1000</div>
        </div>
        <div className="form-group">
          <label>Location *</label>
          <input
            placeholder="e.g. Oak Street, Downtown"
            value={form.location}
            onChange={e => setForm({ ...form, location: e.target.value })}
          />
        </div>
        <div className="form-row">
          <div className="form-group">
            <label>Category</label>
            <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
              <option value="general">General</option>
              <option value="digital_threat">Digital Threat</option>
              <option value="suspicious_activity">Suspicious Activity</option>
              <option value="property_crime">Property Crime</option>
              <option value="infrastructure">Infrastructure</option>
            </select>
          </div>
          <div className="form-group">
            <label>Source</label>
            <select value={form.source} onChange={e => setForm({ ...form, source: e.target.value })}>
              <option value="community_report">Community Report</option>
              <option value="neighborhood_watch">Neighborhood Watch</option>
              <option value="local_police">Local Police</option>
            </select>
          </div>
        </div>
        {error && <div className="form-error">⚠ {error}</div>}
        <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Report →'}
        </button>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('');
  const [filterSev, setFilterSev] = useState('');
  const [checklist, setChecklist] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const [location, setLocation] = useState('My Neighborhood');
  const [toast, setToast] = useState('');
  const [tab, setTab] = useState('alerts');

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  };

  const loadAlerts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const filters = {};
      if (filterCat) filters.category = filterCat;
      if (filterSev) filters.severity = filterSev;
      const data = await fetchAlerts(filters);
      setAlerts(data.alerts || []);
    } catch (e) {
      setError('Could not load alerts. Is the backend running?');
    } finally {
      setLoading(false);
    }
  }, [filterCat, filterSev]);

  useEffect(() => { loadAlerts(); }, [loadAlerts]);

  const handleChecklist = async (category, description) => {
    try {
      const data = await generateChecklist(category, description);
      setChecklist(data);
    } catch (e) {
      showToast('Could not generate checklist. Try again.');
    }
  };

  const handleVerify = async (id) => {
    try {
      await updateAlert(id, { verified: true });
      setAlerts(prev => prev.map(a => a.id === id ? { ...a, verified: true } : a));
      showToast('✓ Alert marked as verified');
    } catch (e) {
      showToast('Failed to update alert');
    }
  };

  const handleSubmitReport = async (data) => {
    const result = await createAlert(data);
    showToast('✓ Report submitted and analyzed by AI');
    await loadAlerts();
    return result;
  };

  const filtered = alerts.filter(a => {
    if (!search) return true;
    return (
      a.raw_text?.toLowerCase().includes(search.toLowerCase()) ||
      a.location?.toLowerCase().includes(search.toLowerCase()) ||
      a.ai_summary?.toLowerCase().includes(search.toLowerCase())
    );
  });

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">🛡</span>
            <span className="logo-text">Community<span className="logo-accent">Guardian</span></span>
          </div>
          <div className="location-selector">
            <span className="loc-icon">📍</span>
            <input
              className="location-input"
              value={location}
              onChange={e => setLocation(e.target.value)}
              placeholder="Your neighborhood"
            />
          </div>
        </div>
        <button className="btn-report" onClick={() => setShowReport(true)}>
          + Report Incident
        </button>
      </header>

      <main className="main">
        {/* Digest Banner */}
        <DigestBanner location={location} />

        {/* Tabs */}
        <div className="tabs">
          <button className={`tab ${tab === 'alerts' ? 'active' : ''}`} onClick={() => setTab('alerts')}>
            Safety Alerts
          </button>
          <button className={`tab ${tab === 'digital' ? 'active' : ''}`} onClick={() => setTab('digital')}>
            Digital Defense
          </button>
        </div>

        {tab === 'alerts' && (
          <>
            {/* Filters */}
            <div className="filters">
              <div className="search-wrap">
                <span className="search-icon">⌕</span>
                <input
                  className="search"
                  placeholder="Search alerts, locations..."
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                />
              </div>
              <select className="filter-select" value={filterCat} onChange={e => setFilterCat(e.target.value)}>
                <option value="">All Categories</option>
                <option value="digital_threat">Digital Threat</option>
                <option value="suspicious_activity">Suspicious Activity</option>
                <option value="property_crime">Property Crime</option>
                <option value="infrastructure">Infrastructure</option>
              </select>
              <select className="filter-select" value={filterSev} onChange={e => setFilterSev(e.target.value)}>
                <option value="">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <button className="btn-ghost" onClick={loadAlerts}>↻ Refresh</button>
            </div>

            {/* Alert List */}
            {loading && <div className="loading-state">Scanning your area...</div>}
            {error && <div className="error-state">⚠ {error}</div>}
            {!loading && !error && filtered.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">🛡️</div>
                <div>No alerts found. Your area looks clear!</div>
              </div>
            )}
            <div className="alert-list">
              {filtered.map(alert => (
                <AlertCard
                  key={alert.id}
                  alert={alert}
                  onChecklist={handleChecklist}
                  onVerify={handleVerify}
                />
              ))}
            </div>
          </>
        )}

        {tab === 'digital' && (
          <div className="digital-defense">
            <h2 className="section-title">Proactive Digital Defense</h2>
            <p className="section-sub">Get an instant action checklist for any digital threat. AI-powered, with rule-based fallback.</p>
            <div className="threat-grid">
              {[
                { type: 'digital_threat', label: '🎣 Phishing Attack', desc: 'Fake emails or messages stealing credentials' },
                { type: 'digital_threat', label: '🔒 Ransomware', desc: 'Malware encrypting your files for ransom' },
                { type: 'digital_threat', label: '📞 Phone Scam', desc: 'Fake IRS, bank, or tech support calls' },
                { type: 'suspicious_activity', label: '👁 Suspicious Activity', desc: 'Unknown persons or vehicles in your area' },
                { type: 'property_crime', label: '🚗 Vehicle Break-In', desc: 'Car theft or break-in in your neighborhood' },
              ].map(t => (
                <div key={t.label} className="threat-card" onClick={() => handleChecklist(t.type, t.desc)}>
                  <div className="threat-label">{t.label}</div>
                  <div className="threat-desc">{t.desc}</div>
                  <div className="threat-cta">Get 5-step checklist →</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      {checklist && <ChecklistModal checklist={checklist} onClose={() => setChecklist(null)} />}
      {showReport && <ReportForm onSubmit={handleSubmitReport} onClose={() => setShowReport(false)} />}

      {/* Toast */}
      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
