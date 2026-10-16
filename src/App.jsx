import React, { useMemo, useState } from 'react'
import Plot from 'react-plotly.js'
import Papa from 'papaparse'
import {
  Activity, ArrowUpRight, BarChart3, Bell, BrainCircuit, ChevronDown,
  CircleDollarSign, Database, FileUp, Filter, LayoutDashboard, Search,
  Settings2, ShieldCheck, SlidersHorizontal, Sparkles, Target, Users, X
} from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const expectedColumns = [
  'recency', 'history', 'used_discount', 'used_bogo', 'zip_code',
  'is_referral', 'channel', 'offer', 'conversion'
]

function formatNumber(value) {
  if (value === null || value === undefined || value === '' || !Number.isFinite(Number(value))) return '—'
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function findIteKey(rows) {
  if (!rows.length) return null
  const candidates = ['ite', 'ite_score', 'individual_treatment_effect', 'treatment_effect', 'uplift_score']
  return candidates.find(key => Object.keys(rows[0]).some(k => k.toLowerCase() === key)) || null
}

function Metric({ label, value, note, icon: Icon, tone = 'blue' }) {
  return <div className="metric-card">
    <div className={`metric-icon ${tone}`}><Icon size={18} /></div>
    <div className="metric-label">{label}</div>
    <div className="metric-value">{value}</div>
    <div className="metric-note">{note}</div>
  </div>
}

function EmptyChart({ title, description }) {
  return <div className="empty-chart">
    <div className="empty-chart-icon"><BarChart3 size={24} /></div>
    <strong>{title}</strong>
    <p>{description}</p>
    <span className="status-pill"><span className="status-dot" /> Waiting for model output</span>
  </div>
}

export default function App() {
  const [fileName, setFileName] = useState('')
  const [rows, setRows] = useState([])
  const [columns, setColumns] = useState([])
  const [uploadMessage, setUploadMessage] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [budget, setBudget] = useState('10000')
  const [maxOfferCost, setMaxOfferCost] = useState('20')
  const [targetGroup, setTargetGroup] = useState('all')
  const [optimization, setOptimization] = useState(null)
  const [optimizing, setOptimizing] = useState(false)
  const [optimizationError, setOptimizationError] = useState('')
  const [search, setSearch] = useState('')
  const [offerFilter, setOfferFilter] = useState('all')
  const [sortDirection, setSortDirection] = useState('desc')
  const [activeTab, setActiveTab] = useState('overview')
  const [apiStatus, setApiStatus] = useState('not checked')

  const iteKey = useMemo(() => findIteKey(optimization?.customers || rows), [optimization, rows])
  const customers = useMemo(() => {
    const source = optimization?.customers || rows
    if (!iteKey) return []
    return source.map((r, index) => ({
      ...r,
      __id: r.customer_id ?? r.customerId ?? r.id ?? `Row ${index + 1}`,
      __ite: Number(r[Object.keys(r).find(k => k.toLowerCase() === iteKey)])
    })).filter(r => Number.isFinite(r.__ite))
  }, [optimization, rows, iteKey])

  const filteredCustomers = useMemo(() => {
    let result = customers.filter(row => String(row.__id).toLowerCase().includes(search.toLowerCase()))
    if (offerFilter !== 'all') result = result.filter(row => String(row.offer || '').toLowerCase() === offerFilter.toLowerCase())
    return [...result].sort((a, b) => sortDirection === 'desc' ? b.__ite - a.__ite : a.__ite - b.__ite)
  }, [customers, search, offerFilter, sortDirection])

  const chart = optimization?.qini || optimization?.uplift_curve || null
  const hasChart = chart && Array.isArray(chart.x) && Array.isArray(chart.model) && Array.isArray(chart.random)

  function handleFile(event) {
    const file = event.target.files?.[0]
    if (!file) return
    setFileName(file.name)
    setUploadMessage('')
    setUploadError('')
    setOptimization(null)
    setOptimizationError('')
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

  async function checkApi() {
    setApiStatus('checking')
    try {
      const response = await fetch(`${API_BASE}/health`)
      if (!response.ok) throw new Error('Health endpoint did not return success')
      setApiStatus('connected')
    } catch {
      setApiStatus('offline')
    }
  }

  async function runOptimization(event) {
    event.preventDefault()
    setOptimizationError('')
    if (!rows.length) {
      setOptimizationError('Upload the retail CSV first.')
      return
    }
    setOptimizing(true)
    try {
      const response = await fetch(`${API_BASE}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          budget: Number(budget),
          max_offer_cost: Number(maxOfferCost),
          target_group: targetGroup,
          rows,
          columns
        })
      })
      if (!response.ok) throw new Error(`Backend returned ${response.status}. Confirm that /api/optimize is implemented by your team.`)
      const result = await response.json()
      setOptimization(result)
      if (!result.customers && !result.qini && !result.uplift_curve) {
        setOptimizationError('The API responded, but did not return customer ITE scores or curve data. Check the response contract in README.md.')
      }
    } catch (error) {
      setOptimizationError(`${error.message}. The dashboard and CSV preview work locally; causal scores and optimized allocation require the team's backend API.`)
    } finally {
      setOptimizing(false)
    }
  }

  const conversions = rows.length && rows.some(r => Object.prototype.hasOwnProperty.call(r, 'conversion'))
    ? rows.filter(r => Number(r.conversion) === 1).length : null
  const conversionRate = rows.length && conversions !== null ? `${(conversions / rows.length * 100).toFixed(1)}%` : '—'
  const offers = [...new Set(rows.map(r => r.offer).filter(Boolean))]

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
        <button className="nav-item muted" onClick={() => setActiveTab('settings')}><Settings2 size={18} /> Settings</button>
        <div className="profile"><div className="avatar">EC</div><div className="profile-copy"><strong>Project workspace</strong><span>Team dashboard</span></div><ChevronDown size={16} /></div>
      </div>
    </aside>

    <main className="main">
      <header className="topbar">
        <div className="breadcrumbs">Workspace <span>/</span> <strong>{activeTab === 'customers' ? 'Customer ITEs' : activeTab === 'optimization' ? 'Budget optimizer' : activeTab === 'settings' ? 'Settings' : 'Overview'}</strong></div>
        <div className="top-actions">
          <div className={`api-indicator ${apiStatus}`}><span /> API {apiStatus === 'connected' ? 'connected' : apiStatus === 'offline' ? 'offline' : apiStatus === 'checking' ? 'checking…' : 'not checked'}</div>
          <button className="icon-button" aria-label="Check backend status" onClick={checkApi}><Bell size={17} /></button>
          <div className="top-avatar">B</div>
        </div>
      </header>

      <div className="page-content">
        {activeTab === 'settings' ? <section className="panel settings-panel">
          <div className="section-eyebrow">CONFIGURATION</div><h1>Workspace settings</h1>
          <p className="subheading">The frontend expects the team's API to run at <code>{API_BASE}</code>.</p>
          <div className="info-box"><ShieldCheck size={18} /><div><strong>Data integrity</strong><p>No causal effect, Qini value, ROI, or savings is invented in this interface. Those values appear only when returned by the model API.</p></div></div>
          <button className="primary-button" onClick={checkApi}>Check backend connection</button>
        </section> : <>
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

          {uploadMessage && <div className="notice success"><Database size={17} /><div><strong>{uploadMessage}</strong><span>CSV is loaded in this browser for preview.</span></div><button onClick={() => {setRows([]);setColumns([]);setFileName('');setUploadMessage('');setOptimization(null)}} aria-label="Clear dataset"><X size={16} /></button></div>}
          {uploadError && <div className="notice warning"><ShieldCheck size={17} /><span>{uploadError}</span></div>}

          {activeTab === 'overview' && <>
            <section className="content-grid">
              <div className="panel chart-panel">
                <div className="panel-heading"><div><h2>Qini / uplift gain curve</h2><p>Model performance compared with random targeting</p></div><span className="mini-label">CAUSAL EVALUATION</span></div>
                {hasChart ? <Plot
                  data={[
                    { x: chart.x, y: chart.model, type: 'scatter', mode: 'lines', name: 'Causal model', line: { color: '#5b5ce2', width: 3 }, fill: 'tozeroy', fillcolor: 'rgba(91,92,226,0.08)' },
                    { x: chart.x, y: chart.random, type: 'scatter', mode: 'lines', name: 'Random rollout', line: { color: '#a5adbd', width: 2, dash: 'dash' } }
                  ]}
                  layout={{ autosize: true, height: 280, margin: { l: 45, r: 20, t: 18, b: 45 }, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { family: 'Inter, sans-serif', color: '#64708a', size: 11 }, xaxis: { title: 'Fraction of customers targeted', gridcolor: '#eef0f6', zeroline: false }, yaxis: { title: 'Cumulative uplift / gain', gridcolor: '#eef0f6', zeroline: false }, legend: { orientation: 'h', y: -0.25 } }}
                  config={{ responsive: true, displayModeBar: false }} style={{ width: '100%' }} useResizeHandler
                /> : <EmptyChart title="Curve appears after model evaluation" description="Upload the dataset, then connect the trained model API. This chart will use the model's Qini/uplift output and random baseline—no placeholder curve is shown." />}
              </div>
              <div className="panel budget-panel">
                <div className="panel-heading"><div><h2>Campaign constraints</h2><p>Set limits for the optimization run</p></div><div className="round-icon"><SlidersHorizontal size={18} /></div></div>
                <form onSubmit={runOptimization}>
                  <label className="field-label" htmlFor="budget">Total campaign budget <span>₹</span></label>
                  <div className="input-wrap"><CircleDollarSign size={17} /><input id="budget" type="number" min="0" step="100" required value={budget} onChange={e => setBudget(e.target.value)} /></div>
                  <label className="field-label" htmlFor="offer-cost">Maximum cost per offer <span>₹</span></label>
                  <div className="input-wrap"><CircleDollarSign size={17} /><input id="offer-cost" type="number" min="0" step="1" required value={maxOfferCost} onChange={e => setMaxOfferCost(e.target.value)} /></div>
                  <label className="field-label" htmlFor="target-group">Customer group</label>
                  <select id="target-group" value={targetGroup} onChange={e => setTargetGroup(e.target.value)}>
                    <option value="all">All eligible customers</option><option value="persuadables">Persuadables</option><option value="sure_things">Sure Things</option><option value="lost_causes">Lost Causes</option><option value="sleeping_dogs">Sleeping Dogs</option>
                  </select>
                  <button className="primary-button full" disabled={optimizing}>{optimizing ? 'Optimizing…' : <><Sparkles size={16} /> Run budget optimization</>}</button>
                </form>
                <p className="footnote">Requires the backend optimization endpoint and trained causal outputs.</p>
                {optimizationError && <div className="inline-error">{optimizationError}</div>}
              </div>
            </section>
            <section className="panel dataset-panel">
              <div className="panel-heading"><div><h2>Dataset preview</h2><p>First 8 rows of the uploaded CSV</p></div><span className="mini-label">{columns.length || 0} COLUMNS</span></div>
              {rows.length ? <div className="table-scroll"><table><thead><tr>{columns.slice(0, 9).map(col => <th key={col}>{col.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{rows.slice(0, 8).map((row, i) => <tr key={i}>{columns.slice(0, 9).map(col => <td key={col}>{String(row[col] ?? '—')}</td>)}</tr>)}</tbody></table></div> : <div className="upload-empty"><div className="upload-empty-icon"><FileUp size={23} /></div><strong>No dataset uploaded yet</strong><p>Choose the team's retail CSV to preview the columns and row count.</p><label className="secondary-button">Choose CSV<input type="file" accept=".csv,text/csv" onChange={handleFile} hidden /></label></div>}
            </section>
          </>}

          {activeTab === 'customers' && <section className="panel customer-panel">
            <div className="panel-heading"><div><h2>Individual treatment effects</h2><p>Search and filter customer-level model outputs</p></div><span className="mini-label">{customers.length} SCORES</span></div>
            <div className="table-controls">
              <div className="search-box"><Search size={17} /><input placeholder="Search customer ID…" value={search} onChange={e => setSearch(e.target.value)} /></div>
              <div className="select-box"><Filter size={16} /><select value={offerFilter} onChange={e => setOfferFilter(e.target.value)}><option value="all">All offers</option>{offers.map(o => <option key={o} value={o}>{o}</option>)}</select></div>
              <button className="sort-button" onClick={() => setSortDirection(s => s === 'desc' ? 'asc' : 'desc')}>ITE {sortDirection === 'desc' ? '↓' : '↑'}</button>
            </div>
            {customers.length ? <div className="table-scroll"><table><thead><tr><th>Customer ID</th><th>Offer</th><th>Individual treatment effect</th><th>Targeting signal</th></tr></thead><tbody>{filteredCustomers.slice(0, 100).map((row, i) => <tr key={`${row.__id}-${i}`}><td className="customer-id">{row.__id}</td><td>{row.offer || '—'}</td><td className={row.__ite >= 0 ? 'positive' : 'negative'}>{formatNumber(row.__ite)}</td><td><span className={`signal ${row.__ite > 0 ? 'good' : row.__ite < 0 ? 'bad' : 'neutral'}`}>{row.__ite > 0 ? 'Positive uplift' : row.__ite < 0 ? 'Negative uplift' : 'No estimated effect'}</span></td></tr>)}</tbody></table><div className="table-footer">Showing {Math.min(filteredCustomers.length, 100)} of {filteredCustomers.length} matching scores</div></div> : <div className="upload-empty"><div className="upload-empty-icon"><BrainCircuit size={23} /></div><strong>No genuine ITE scores available yet</strong><p>The retail CSV contains customer features and conversion outcomes, but ITE scores must be generated by the team's trained causal model. Once the API returns customer rows with an <code>ite</code> or <code>treatment_effect</code> field, this searchable table will populate.</p><button className="secondary-button" onClick={() => setActiveTab('overview')}>Go to dashboard</button></div>}
          </section>}

          {activeTab === 'optimization' && <section className="panel optimization-panel">
            <div className="panel-heading"><div><h2>Budget allocation results</h2><p>Allocation returned by the team's constrained optimizer</p></div><span className="mini-label">SCI-PY / BACKEND</span></div>
            {optimization?.allocation?.length ? <div className="table-scroll"><table><thead><tr>{Object.keys(optimization.allocation[0]).map(key => <th key={key}>{key.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{optimization.allocation.map((row, i) => <tr key={i}>{Object.keys(optimization.allocation[0]).map(key => <td key={key}>{String(row[key] ?? '—')}</td>)}</tr>)}</tbody></table></div> : <div className="upload-empty"><div className="upload-empty-icon"><Target size={23} /></div><strong>No allocation generated yet</strong><p>Set the budget constraints on Overview and run optimization. The table appears only after the backend returns real allocation results.</p><button className="secondary-button" onClick={() => setActiveTab('overview')}>Set campaign constraints</button></div>}
            {optimization?.summary && <div className="result-summary">{Object.entries(optimization.summary).map(([key, value]) => <div key={key}><span>{key.replaceAll('_', ' ')}</span><strong>{String(value)}</strong></div>)}</div>}
            {optimizationError && <div className="inline-error">{optimizationError}</div>}
          </section>}
        </>}
        <footer className="footer"><span>ECONOCAUSAL · DYNAMIC PRICING VIA DOUBLE MACHINE LEARNING</span><span><span className="footer-dot" /> Data stays in this browser until you send an API request</span></footer>
      </div>
    </main>
  </div>
}