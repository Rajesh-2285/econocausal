import React, { useState } from 'react'
import {
  Activity, BarChart3, Bell, BrainCircuit, ChevronDown,
  LayoutDashboard, Settings2, Sparkles, Target, Users
} from 'lucide-react'

function formatNumber(value) {
  if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—'
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function Metric({ label, value, note, icon: Icon, tone = 'blue' }) {
  return <div className="metric-card">
    <div className={`metric-icon ${tone}`}><Icon size={18} /></div>
    <div className="metric-label">{label}</div>
    <div className="metric-value">{value}</div>
    <div className="metric-note">{note}</div>
  </div>
}

export default function App() {
  const [activeTab, setActiveTab] = useState('overview')
  const [rows, setRows] = useState([])
  const [fileName, setFileName] = useState('')

  const conversions = null
  const conversionRate = '—'
  const customers = []

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={22} strokeWidth={2.5} /></div>
          <div><div className="brand-name">EconoCausal</div><div className="brand-sub">CAUSAL PRICING ENGINE</div></div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          <button className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}><LayoutDashboard size={18} /> Overview</button>
          <button className={`nav-item ${activeTab === 'customers' ? 'active' : ''}`} onClick={() => setActiveTab('customers')}><Users size={18} /> Customer ITEs <span className="nav-count">{customers.length || '—'}</span></button>
          <button className={`nav-item ${activeTab === 'optimization' ? 'active' : ''}`} onClick={() => setActiveTab('optimization')}><Target size={18} /> Budget optimizer</button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-tip"><div className="tip-icon"><Sparkles size={16} /></div><strong>Make every offer count.</strong><p>Target customers whose behaviour can actually be changed by an offer.</p></div>
          <button className={`nav-item muted ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}><Settings2 size={18} /> Settings</button>
          <div className="profile"><div className="avatar">EC</div><div className="profile-copy"><strong>Project workspace</strong><span>Team dashboard</span></div><ChevronDown size={16} /></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs">Workspace <span>/</span> <strong>{activeTab === 'customers' ? 'Customer ITEs' : activeTab === 'optimization' ? 'Budget optimizer' : activeTab === 'settings' ? 'Settings' : 'Overview'}</strong></div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Check backend status"><Bell size={17} /></button>
            <div className="top-avatar">B</div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div><div className="section-eyebrow">DYNAMIC PRICING INTELLIGENCE</div><h1>{activeTab === 'customers' ? 'Customer-level treatment effects' : activeTab === 'optimization' ? 'Budget optimization' : 'Causal impact overview'}</h1>
              <p className="subheading">Use causal effects—not just conversion predictions—to decide who should receive an offer.</p></div>
          </section>

          <section className="metrics-grid">
            <Metric label="CUSTOMERS LOADED" value={rows.length ? formatNumber(rows.length) : '—'} note={fileName || 'Upload a CSV to begin'} icon={Users} tone="blue" />
            <Metric label="OBSERVED CONVERSIONS" value={conversions === null ? '—' : formatNumber(conversions)} note="From conversion = 1 in uploaded data" icon={Activity} tone="green" />
            <Metric label="CONVERSION RATE" value={conversionRate} note="Descriptive, not causal uplift" icon={BarChart3} tone="purple" />
            <Metric label="MODEL ITE SCORES" value={customers.length ? formatNumber(customers.length) : '—'} note={customers.length ? 'Received from model/API output' : 'Awaiting trained causal model'} icon={BrainCircuit} tone="orange" />
          </section>
        </div>
      </main>
    </div>
  )
}
