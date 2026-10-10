import React from 'react'
import {
  Activity, Bell, ChevronDown, LayoutDashboard,
  Settings2, Sparkles, Target, Users
} from 'lucide-react'

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={22} strokeWidth={2.5} /></div>
          <div><div className="brand-name">EconoCausal</div><div className="brand-sub">CAUSAL PRICING ENGINE</div></div>
        </div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="nav-list">
          <button className="nav-item active"><LayoutDashboard size={18} /> Overview</button>
          <button className="nav-item"><Users size={18} /> Customer ITEs</button>
          <button className="nav-item"><Target size={18} /> Budget optimizer</button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-tip"><div className="tip-icon"><Sparkles size={16} /></div><strong>Make every offer count.</strong><p>Target customers whose behaviour can actually be changed by an offer.</p></div>
          <button className="nav-item muted"><Settings2 size={18} /> Settings</button>
          <div className="profile"><div className="avatar">EC</div><div className="profile-copy"><strong>Project workspace</strong><span>Team dashboard</span></div><ChevronDown size={16} /></div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs">Workspace <span>/</span> <strong>Overview</strong></div>
          <div className="top-actions">
            <button className="icon-button" aria-label="Check backend status"><Bell size={17} /></button>
            <div className="top-avatar">B</div>
          </div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div><div className="section-eyebrow">DYNAMIC PRICING INTELLIGENCE</div><h1>Causal impact overview</h1>
              <p className="subheading">Use causal effects—not just conversion predictions—to decide who should receive an offer.</p></div>
          </section>
        </div>
      </main>
    </div>
  )
}
