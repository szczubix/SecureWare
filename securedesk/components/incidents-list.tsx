'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { formatDate, SEVERITY_LABELS, STATUS_LABELS, CATEGORY_LABELS } from '@/lib/utils'

interface Incident {
  id: string
  incidentNumber: string
  title: string
  description: string
  severity: string
  status: string
  category: string
  reportedBy: string
  assignedTo: string | null
  nis2Active: boolean
  createdAt: string
  _count: { evidences: number }
}

const SEVERITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  HIGH: { bg: 'rgba(249,115,22,0.15)', text: '#fdba74', border: 'rgba(249,115,22,0.25)' },
  MEDIUM: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  LOW: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
}

const STATUS_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NEW: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  IN_PROGRESS: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  ANALYSIS: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  CLOSED: { bg: 'rgba(34,197,94,0.15)', text: '#86efac', border: 'rgba(34,197,94,0.25)' },
}

interface StatsData {
  open: number
  nis2: number
  closedLast30: number
  overdue: number
}

export function IncidentsList() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [stats, setStats] = useState<StatsData>({ open: 0, nis2: 0, closedLast30: 0, overdue: 0 })
  const [filter, setFilter] = useState<string>('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const fetchIncidents = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filter === 'open') params.set('status', 'NEW')
    if (filter === 'nis2') params.set('nis2', 'true')
    if (filter === 'critical') params.set('severity', 'CRITICAL')
    if (filter === 'closed') params.set('status', 'CLOSED')
    if (search) params.set('search', search)

    const res = await fetch(`/api/incidents?${params}`)
    const data = await res.json()
    setIncidents(data.data || [])
    setLoading(false)
  }, [filter, search])

  useEffect(() => {
    fetchIncidents()
  }, [fetchIncidents])

  useEffect(() => {
    async function loadStats() {
      const [allRes, nis2Res, closedRes] = await Promise.all([
        fetch('/api/incidents'),
        fetch('/api/incidents?nis2=true'),
        fetch('/api/incidents?status=CLOSED'),
      ])
      const [all, nis2data, closedData] = await Promise.all([
        allRes.json(), nis2Res.json(), closedRes.json(),
      ])
      const allIncidents: Incident[] = all.data || []
      const openCount = allIncidents.filter((i) => i.status !== 'CLOSED').length
      const closedLast30 = (closedData.data || []).filter((i: Incident) => {
        const d = new Date(i.createdAt)
        return Date.now() - d.getTime() < 30 * 24 * 60 * 60 * 1000
      }).length
      setStats({
        open: openCount,
        nis2: (nis2data.data || []).length,
        closedLast30,
        overdue: 0,
      })
    }
    loadStats()
  }, [incidents])

  const filters = [
    { key: 'all', label: 'Wszystkie' },
    { key: 'open', label: 'Otwarte' },
    { key: 'nis2', label: 'NIS2' },
    { key: 'critical', label: 'Krytyczne' },
    { key: 'closed', label: 'Zamknięte' },
  ]

  return (
    <div style={{ padding: '24px', flex: 1 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Incydenty</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>
            Zarządzanie incydentami bezpieczeństwa informacji
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          style={{
            padding: '8px 16px',
            background: '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 500,
            cursor: 'pointer',
          }}
        >
          + Nowy incydent
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
        {[
          { label: 'Otwarte', value: stats.open, color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
          { label: 'NIS2 aktywny', value: stats.nis2, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
          { label: 'Zamknięte 30 dni', value: stats.closedLast30, color: '#22c55e', bg: 'rgba(34,197,94,0.1)' },
          { label: 'Przeterminowane', value: stats.overdue, color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
        ].map((stat) => (
          <div key={stat.label} style={{
            background: '#161922',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '8px',
            padding: '16px',
          }}>
            <div style={{ fontSize: '28px', fontWeight: 600, color: stat.color, fontFamily: 'IBM Plex Mono, monospace' }}>
              {stat.value}
            </div>
            <div style={{ fontSize: '12px', color: '#8b90a0', marginTop: '4px' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filters + Search */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '4px' }}>
          {filters.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              style={{
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                border: filter === f.key ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)',
                background: filter === f.key ? 'rgba(59,130,246,0.1)' : 'transparent',
                color: filter === f.key ? '#93c5fd' : '#8b90a0',
                cursor: 'pointer',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
        <input
          type="text"
          placeholder="Szukaj incydentów..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            padding: '7px 12px',
            background: '#161922',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: '6px',
            color: '#e8eaf0',
            fontSize: '13px',
            outline: 'none',
          }}
        />
      </div>

      {/* Table */}
      <div style={{
        background: '#161922',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              {['ID', 'Incydent', 'Klasyfikacja', 'Status', 'NIS2', 'Data'].map((col) => (
                <th key={col} style={{
                  padding: '10px 16px',
                  textAlign: 'left',
                  fontSize: '11px',
                  color: '#555b6e',
                  fontFamily: 'IBM Plex Mono, monospace',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  fontWeight: 500,
                }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>
                  Ładowanie...
                </td>
              </tr>
            ) : incidents.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>
                  Brak incydentów spełniających kryteria
                </td>
              </tr>
            ) : incidents.map((incident) => {
              const sevColor = SEVERITY_COLORS[incident.severity] || SEVERITY_COLORS.LOW
              const stColor = STATUS_COLORS[incident.status] || STATUS_COLORS.NEW
              return (
                <tr
                  key={incident.id}
                  style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <Link href={`/incidents/${incident.id}`} style={{ textDecoration: 'none' }}>
                      <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>
                        {incident.incidentNumber}
                      </span>
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px', maxWidth: '320px' }}>
                    <Link href={`/incidents/${incident.id}`} style={{ textDecoration: 'none' }}>
                      <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500, marginBottom: '3px' }}>
                        {incident.title}
                      </div>
                      <div style={{ fontSize: '11px', color: '#555b6e' }}>
                        {CATEGORY_LABELS[incident.category]} · zgł. {incident.reportedBy}
                        {incident._count.evidences > 0 && ` · ${incident._count.evidences} dowodów`}
                      </div>
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'IBM Plex Mono, monospace',
                      background: sevColor.bg,
                      color: sevColor.text,
                      border: `1px solid ${sevColor.border}`,
                    }}>
                      {SEVERITY_LABELS[incident.severity]}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontFamily: 'IBM Plex Mono, monospace',
                      background: stColor.bg,
                      color: stColor.text,
                      border: `1px solid ${stColor.border}`,
                    }}>
                      {STATUS_LABELS[incident.status]}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {incident.nis2Active ? (
                      <span style={{
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontFamily: 'IBM Plex Mono, monospace',
                        background: 'rgba(245,158,11,0.15)',
                        color: '#fcd34d',
                        border: '1px solid rgba(245,158,11,0.25)',
                      }}>
                        NIS2
                      </span>
                    ) : (
                      <span style={{ color: '#3a3f52', fontSize: '11px' }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {formatDate(incident.createdAt)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {showForm && (
        <NewIncidentModal
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); fetchIncidents() }}
        />
      )}
    </div>
  )
}

function NewIncidentModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    title: '',
    description: '',
    severity: 'HIGH',
    category: 'OTHER',
    reportedBy: '',
    nis2Active: false,
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const res = await fetch('/api/incidents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (res.ok) {
      onCreated()
    } else {
      const data = await res.json()
      setError(data.error?.formErrors?.[0] || 'Błąd podczas tworzenia incydentu')
      setLoading(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50,
    }}>
      <div style={{
        background: '#161922', border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '10px', padding: '32px', width: '540px', maxWidth: '95vw',
      }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#e8eaf0', marginBottom: '24px' }}>
          Nowy incydent bezpieczeństwa
        </h2>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <FormField label="Tytuł incydentu">
              <input
                required
                minLength={3}
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder="Krótki opis zdarzenia..."
                style={inputStyle}
              />
            </FormField>
            <FormField label="Opis zdarzenia">
              <textarea
                required
                minLength={10}
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Szczegółowy opis incydentu..."
                style={{ ...inputStyle, resize: 'vertical' }}
              />
            </FormField>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <FormField label="Klasyfikacja">
                <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} style={inputStyle}>
                  <option value="CRITICAL">Krytyczny</option>
                  <option value="HIGH">Wysoki</option>
                  <option value="MEDIUM">Średni</option>
                  <option value="LOW">Niski</option>
                </select>
              </FormField>
              <FormField label="Kategoria">
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} style={inputStyle}>
                  <option value="UNAUTHORIZED_ACCESS">Nieautoryzowany dostęp</option>
                  <option value="DATA_LEAK">Wyciek danych</option>
                  <option value="AVAILABILITY">Niedostępność</option>
                  <option value="PHISHING">Phishing</option>
                  <option value="MALWARE">Złośliwe oprogramowanie</option>
                  <option value="PHYSICAL">Incydent fizyczny</option>
                  <option value="OTHER">Inne</option>
                </select>
              </FormField>
            </div>
            <FormField label="Zgłaszający">
              <input
                required
                value={form.reportedBy}
                onChange={(e) => setForm({ ...form, reportedBy: e.target.value })}
                placeholder="Imię i nazwisko zgłaszającego"
                style={inputStyle}
              />
            </FormField>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={form.nis2Active}
                onChange={(e) => setForm({ ...form, nis2Active: e.target.checked })}
              />
              <span style={{ fontSize: '13px', color: '#8b90a0' }}>
                Incydent podlega raportowaniu NIS2 (Art. 21)
              </span>
            </label>
          </div>

          {error && (
            <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: '8px', marginTop: '24px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>
              Anuluj
            </button>
            <button type="submit" disabled={loading} style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Tworzenie...' : 'Utwórz incydent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  background: '#0f1117',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '6px',
  color: '#e8eaf0',
  fontSize: '13px',
  outline: 'none',
  boxSizing: 'border-box',
}

function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', marginBottom: '6px', fontFamily: 'IBM Plex Mono, monospace' }}>
        {label}
      </label>
      {children}
    </div>
  )
}
