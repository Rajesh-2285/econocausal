import React, { useState } from 'react'
import Papa from 'papaparse'
import {
  Activity, BarChart3, Bell, BrainCircuit, ChevronDown, Database,
  FileUp, LayoutDashboard, Settings2, ShieldCheck, Sparkles, Target, Users, X
} from 'lucide-react'

const expectedColumns = [
  'recency', 'history', 'used_discount', 'used_bogo', 'zip_code',
  'is_referral', 'channel', 'offer', 'conversion'
]

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
  const [fileName, setFileName] = useState('')
  const [rows, setRows] = useState([])
  const [columns, setColumns] = useState([])
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [activeTab, setActiveTab] = useState('overview')

  function handleFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setUploadMessage('')
    setUploadError('')
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
      complete: ({ data, meta, errors }) => {
        if (errors?.length) setUploadError(`CSV parsed with ${errors.length} warning(s). Check the preview before using it.`)
        const validRows = data.filter(row => Object.values(row).some(value => value !== '' && value !== null && value !== undefined))
        const cols = meta.fields || Object.keys(validRows[0] || {})
        setRows(validRows)
        setColumns(cols)
        const missing = expectedColumns.filter(c => !cols.includes(c))
        setUploadMessage(`${validRows.length.toLocaleString()} rows · ${cols.length} columns loaded`)
        if (missing.length) {
          setUploadError(`Loaded successfully, but expected retail fields not found: ${missing.join(', ')}. Confirm your CSV schema with the team before model analysis.`)
        }
      },
      error: error => setUploadError(error.message || 'Could not read this CSV file.')
    })
    event.target.value = ''
  }

  const conversions = rows.length && rows.some(r => Object.prototype.hasOwnProperty.call(r, 'conversion'))
    ? rows.filter(r => Number(r.conversion) === 1).length : null
  const conversionRate = rows.length && conversions !== null ? `${(conversions / rows.length * 100).toFixed(1)}%` : '—'
  const customers = []

  return <div className="app-shell">
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
          <label className="upload-button"><FileUp size={17} /> Upload dataset<input type="file" accept=".csv,text/csv" onChange={handleFile} hidden /></label>
        </section>

        <section className="metrics-grid">
          <Metric label="CUSTOMERS LOADED" value={rows.length ? formatNumber(rows.length) : '—'} note={fileName || 'Upload a CSV to begin'} icon={Users} tone="blue" />
          <Metric label="OBSERVED CONVERSIONS" value={conversions === null ? '—' : formatNumber(conversions)} note="From conversion = 1 in uploaded data" icon={Activity} tone="green" />
          <Metric label="CONVERSION RATE" value={conversionRate} note="Descriptive, not causal uplift" icon={BarChart3} tone="purple" />
          <Metric label="MODEL ITE SCORES" value={customers.length ? formatNumber(customers.length) : '—'} note={customers.length ? 'Received from model/API output' : 'Awaiting trained causal model'} icon={BrainCircuit} tone="orange" />
        </section>

        {uploadMessage && <div className="notice success"><Database size={17} /><div><strong>{uploadMessage}</strong><span>CSV is loaded in this browser for preview.</span></div><button onClick={() => {setRows([]);setColumns([]);setFileName('');setUploadMessage('')}} aria-label="Clear dataset"><X size={16} /></button></div>}
        {uploadError && <div className="notice warning"><ShieldCheck size={17} /><span>{uploadError}</span></div>}
      </div>
    </main>
  </div>
}
