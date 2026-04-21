'use client'

import { useState, useEffect, useCallback } from 'react'
import { THEME_LABELS, type ControlTheme } from '@/lib/iso-controls'

type ControlStatus = 'NOT_REVIEWED' | 'APPLICABLE' | 'PLANNED' | 'EXCLUDED' | 'NOT_APPLICABLE'

interface Control {
  number: string
  theme: ControlTheme
  title: string
  status: ControlStatus
  justification: string | null
  owner: string | null
  updatedAt: string | null
}

interface Stats {
  total: number
  applicable: number
  planned: number
  excluded: number
  notApplicable: number
  notReviewed: number
}

const STATUS_META: Record<ControlStatus, { label: string; color: string; bg: string; border: string }> = {
  NOT_REVIEWED: { label: 'Nie oceniono', color: '#555b6e', bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.08)' },
  APPLICABLE:   { label: 'Wdrożona',     color: '#86efac', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.3)' },
  PLANNED:      { label: 'Planowana',    color: '#93c5fd', bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.3)' },
  EXCLUDED:     { label: 'Wykluczona',   color: '#fca5a5', bg: 'rgba(239,68,68,0.15)',  border: 'rgba(239,68,68,0.3)' },
  NOT_APPLICABLE: { label: 'Nie dotyczy', color: '#8b90a0', bg: 'rgba(255,255,255,0.05)', border: 'rgba(255,255,255,0.1)' },
}

const THEMES: ControlTheme[] = ['ORGANIZATIONAL', 'PEOPLE', 'PHYSICAL', 'TECHNOLOGICAL']

function exportCsv(controls: Control[]) {
  const rows = [
    ['Numer', 'Temat', 'Tytuł', 'Status', 'Właściciel', 'Uzasadnienie'],
    ...controls.map(c => [
      c.number,
      THEME_LABELS[c.theme],
      c.title,
      STATUS_META[c.status].label,
      c.owner || '',
      c.justification || '',
    ]),
  ]
  const csv = '﻿' + rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = 'SoA_ISO27001.csv'; a.click()
  URL.revokeObjectURL(url)
}

function StatusChip({ status }: { status: ControlStatus }) {
  const m = STATUS_META[status]
  return (
    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap', background: m.bg, color: m.color, border: `1px solid ${m.border}` }}>
      {m.label}
    </span>
  )
}

function JustificationModal({ control, onClose, onSaved }: {
  control: Control
  onClose: () => void
  onSaved: (updated: Partial<Control>) => void
}) {
  const [justification, setJustification] = useState(control.justification || '')
  const [owner, setOwner] = useState(control.owner || '')
  const [saving, setSaving] = useState(false)

  async function save() {
    setSaving(true)
    const res = await fetch('/api/controls', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ controlNumber: control.number, justification: justification || null, owner: owner || null }),
    })
    if (res.ok) {
      onSaved({ justification: justification || null, owner: owner || null })
      onClose()
    }
    setSaving(false)
  }

  const iStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '20px' }}>
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '28px', width: '520px', maxWidth: '95vw' }}>
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '4px' }}>KONTROLKA {control.number}</div>
          <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>{control.title}</h2>
          <div style={{ marginTop: '8px' }}><StatusChip status={control.status} /></div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '5px' }}>
              {control.status === 'EXCLUDED' || control.status === 'NOT_APPLICABLE' ? 'Uzasadnienie wykluczenia' : 'Opis wdrożenia / uwagi'}
            </label>
            <textarea rows={4} value={justification} onChange={e => setJustification(e.target.value)}
              placeholder="Opisz sposób wdrożenia, uzasadnienie wykluczenia lub inne uwagi..."
              style={{ ...iStyle, resize: 'vertical' }} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '5px' }}>Właściciel kontrolki</label>
            <input value={owner} onChange={e => setOwner(e.target.value)} placeholder="Imię i nazwisko / rola" style={iStyle} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: '8px', marginTop: '20px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>Anuluj</button>
          <button onClick={save} disabled={saving} style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: saving ? 0.7 : 1 }}>
            {saving ? 'Zapisywanie...' : 'Zapisz'}
          </button>
        </div>
      </div>
    </div>
  )
}

export function ControlsList() {
  const [controls, setControls] = useState<Control[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<ControlStatus | ''>('')
  const [filterTheme, setFilterTheme] = useState<ControlTheme | ''>('')
  const [editingJustification, setEditingJustification] = useState<Control | null>(null)
  const [saving, setSaving] = useState<string | null>(null)

  const load = useCallback(async () => {
    const res = await fetch('/api/controls')
    if (res.ok) {
      const json = await res.json()
      setControls(json.data)
      setStats(json.stats)
    }
    setLoading(false)
  }, [])

  useEffect(() => { load() }, [load])

  async function updateStatus(controlNumber: string, status: ControlStatus) {
    setSaving(controlNumber)
    setControls(prev => prev.map(c => c.number === controlNumber ? { ...c, status } : c))
    setStats(prev => {
      if (!prev) return prev
      const old = controls.find(c => c.number === controlNumber)?.status ?? 'NOT_REVIEWED'
      const next = { ...prev }
      const dec = (k: keyof Stats) => { next[k] = Math.max(0, (next[k] as number) - 1) }
      const inc = (k: keyof Stats) => { next[k] = (next[k] as number) + 1 }
      if (old === 'APPLICABLE') dec('applicable')
      else if (old === 'PLANNED') dec('planned')
      else if (old === 'EXCLUDED') dec('excluded')
      else if (old === 'NOT_APPLICABLE') dec('notApplicable')
      else dec('notReviewed')
      if (status === 'APPLICABLE') inc('applicable')
      else if (status === 'PLANNED') inc('planned')
      else if (status === 'EXCLUDED') inc('excluded')
      else if (status === 'NOT_APPLICABLE') inc('notApplicable')
      else inc('notReviewed')
      return next
    })
    await fetch('/api/controls', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ controlNumber, status }),
    })
    setSaving(null)
  }

  function updateJustification(number: string, data: Partial<Control>) {
    setControls(prev => prev.map(c => c.number === number ? { ...c, ...data } : c))
  }

  const filtered = controls.filter(c => {
    if (filterStatus && c.status !== filterStatus) return false
    if (filterTheme && c.theme !== filterTheme) return false
    return true
  })

  const reviewedCount = stats ? stats.applicable + stats.planned + stats.excluded + stats.notApplicable : 0
  const progressPct = stats ? Math.round((reviewedCount / stats.total) * 100) : 0
  const applicablePct = stats ? Math.round((stats.applicable / stats.total) * 100) : 0

  const sel: React.CSSProperties = { padding: '7px 10px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px', outline: 'none' }

  if (loading) return <div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>

  return (
    <div style={{ padding: '24px', flex: 1, minWidth: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '24px', gap: '16px', flexWrap: 'wrap' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Kontrolki ISO 27001:2022 — Annex A</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>Deklaracja stosowalności (SoA) · 93 kontrolki bezpieczeństwa</p>
        </div>
        <button onClick={() => exportCsv(controls)} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px', cursor: 'pointer', whiteSpace: 'nowrap' }}>
          ↓ Eksportuj SoA (CSV)
        </button>
      </div>

      {/* Progress + stats */}
      {stats && (
        <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '10px', padding: '20px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ fontSize: '13px', color: '#8b90a0' }}>
              Oceniono <span style={{ color: '#e8eaf0', fontWeight: 600 }}>{reviewedCount}</span> z <span style={{ color: '#e8eaf0', fontWeight: 600 }}>{stats.total}</span> kontrolek
            </div>
            <div style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>{progressPct}% ukończone</div>
          </div>
          <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden', marginBottom: '14px' }}>
            <div style={{ height: '100%', background: '#3b82f6', borderRadius: '3px', width: `${progressPct}%`, transition: 'width 0.3s' }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: '10px' }}>
            {([
              ['applicable', 'Wdrożone',   STATUS_META.APPLICABLE],
              ['planned',    'Planowane',  STATUS_META.PLANNED],
              ['excluded',   'Wykluczone', STATUS_META.EXCLUDED],
              ['notApplicable', 'Nie dotyczy', STATUS_META.NOT_APPLICABLE],
              ['notReviewed',   'Nie oceniono', STATUS_META.NOT_REVIEWED],
            ] as const).map(([key, label, meta]) => (
              <div key={key} style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => setFilterStatus(filterStatus === key.replace(/([A-Z])/g, '_$1').toUpperCase() as ControlStatus ? '' : key.replace(/([A-Z])/g, '_$1').toUpperCase() as ControlStatus)}>
                <div style={{ fontSize: '22px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: meta.color }}>{stats[key as keyof Stats]}</div>
                <div style={{ fontSize: '11px', color: '#555b6e', marginTop: '2px' }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={filterStatus} onChange={e => setFilterStatus(e.target.value as ControlStatus | '')} style={sel}>
          <option value="">Wszystkie statusy</option>
          <option value="APPLICABLE">Wdrożone</option>
          <option value="PLANNED">Planowane</option>
          <option value="EXCLUDED">Wykluczone</option>
          <option value="NOT_APPLICABLE">Nie dotyczy</option>
          <option value="NOT_REVIEWED">Nie oceniono</option>
        </select>
        <select value={filterTheme} onChange={e => setFilterTheme(e.target.value as ControlTheme | '')} style={sel}>
          <option value="">Wszystkie tematy</option>
          {THEMES.map(t => <option key={t} value={t}>{THEME_LABELS[t]}</option>)}
        </select>
        {(filterStatus || filterTheme) && (
          <button onClick={() => { setFilterStatus(''); setFilterTheme('') }}
            style={{ padding: '6px 12px', background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px', cursor: 'pointer' }}>
            ✕ Wyczyść
          </button>
        )}
        <span style={{ fontSize: '12px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', marginLeft: 'auto' }}>
          {filtered.length} z {controls.length}
        </span>
      </div>

      {/* Grouped by theme */}
      {THEMES.filter(t => !filterTheme || t === filterTheme).map(theme => {
        const themeControls = filtered.filter(c => c.theme === theme)
        if (themeControls.length === 0) return null
        const doneInTheme = themeControls.filter(c => c.status !== 'NOT_REVIEWED').length
        return (
          <div key={theme} style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
              <h2 style={{ fontSize: '13px', fontWeight: 600, color: '#8b90a0', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.06em', margin: 0 }}>
                {THEME_LABELS[theme]}
              </h2>
              <span style={{ fontSize: '11px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace' }}>
                {doneInTheme}/{themeControls.length}
              </span>
            </div>
            <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
                    <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', width: '60px' }}>Nr</th>
                    <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Tytuł kontrolki</th>
                    <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', width: '140px' }}>Status</th>
                    <th style={{ padding: '8px 14px', textAlign: 'left', fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', width: '130px' }}>Właściciel</th>
                    <th style={{ padding: '8px 14px', width: '80px' }} />
                  </tr>
                </thead>
                <tbody>
                  {themeControls.map((control, idx) => (
                    <tr key={control.number}
                      style={{ borderBottom: idx < themeControls.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none' }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                      <td style={{ padding: '11px 14px', fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6', whiteSpace: 'nowrap' }}>
                        {control.number}
                      </td>
                      <td style={{ padding: '11px 14px' }}>
                        <div style={{ fontSize: '13px', color: '#c8ccd6' }}>{control.title}</div>
                        {control.justification && (
                          <div style={{ fontSize: '11px', color: '#555b6e', marginTop: '3px', maxWidth: '400px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {control.justification}
                          </div>
                        )}
                      </td>
                      <td style={{ padding: '11px 14px' }}>
                        <select
                          value={control.status}
                          disabled={saving === control.number}
                          onChange={e => updateStatus(control.number, e.target.value as ControlStatus)}
                          style={{ padding: '4px 8px', background: STATUS_META[control.status].bg, border: `1px solid ${STATUS_META[control.status].border}`, borderRadius: '4px', color: STATUS_META[control.status].color, fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', outline: 'none', cursor: 'pointer', opacity: saving === control.number ? 0.6 : 1 }}>
                          <option value="NOT_REVIEWED">Nie oceniono</option>
                          <option value="APPLICABLE">Wdrożona</option>
                          <option value="PLANNED">Planowana</option>
                          <option value="EXCLUDED">Wykluczona</option>
                          <option value="NOT_APPLICABLE">Nie dotyczy</option>
                        </select>
                      </td>
                      <td style={{ padding: '11px 14px', fontSize: '12px', color: '#555b6e', maxWidth: '130px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {control.owner || <span style={{ color: '#3a3f52' }}>—</span>}
                      </td>
                      <td style={{ padding: '11px 14px', textAlign: 'right' }}>
                        <button onClick={() => setEditingJustification(control)}
                          style={{ padding: '4px 10px', background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '4px', color: '#555b6e', fontSize: '11px', cursor: 'pointer' }}>
                          {control.justification || control.owner ? 'Edytuj' : 'Uzasadnienie'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}

      {editingJustification && (
        <JustificationModal
          control={editingJustification}
          onClose={() => setEditingJustification(null)}
          onSaved={data => {
            updateJustification(editingJustification.number, data)
            setEditingJustification(null)
          }}
        />
      )}
    </div>
  )
}
