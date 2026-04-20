'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
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

interface PagedResponse {
  data: Incident[]
  total: number
  page: number
  pages: number
  stats: { open: number; closed: number }
}

const SEV_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  HIGH: { bg: 'rgba(249,115,22,0.15)', text: '#fdba74', border: 'rgba(249,115,22,0.25)' },
  MEDIUM: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  LOW: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
}

const ST_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NEW: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  IN_PROGRESS: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  ANALYSIS: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  CLOSED: { bg: 'rgba(34,197,94,0.15)', text: '#86efac', border: 'rgba(34,197,94,0.25)' },
}

type SortField = 'createdAt' | 'severity' | 'status' | 'incidentNumber'

function SortIcon({ field, current, dir }: { field: string; current: string; dir: string }) {
  if (field !== current) return <span style={{ color: '#3a3f52', marginLeft: '4px' }}>↕</span>
  return <span style={{ color: '#3b82f6', marginLeft: '4px' }}>{dir === 'asc' ? '↑' : '↓'}</span>
}

export function IncidentsList() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [result, setResult] = useState<PagedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  // Filter state — initialized from URL
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [severity, setSeverity] = useState(searchParams.get('severity') || '')
  const [status, setStatus] = useState(searchParams.get('status') || '')
  const [category, setCategory] = useState(searchParams.get('category') || '')
  const [nis2, setNis2] = useState(searchParams.get('nis2') === 'true')
  const [dateFrom, setDateFrom] = useState(searchParams.get('dateFrom') || '')
  const [dateTo, setDateTo] = useState(searchParams.get('dateTo') || '')
  const [sortBy, setSortBy] = useState<SortField>((searchParams.get('sortBy') as SortField) || 'createdAt')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(searchParams.get('sortDir') === 'asc' ? 'asc' : 'desc')
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10))

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [debouncedSearch, setDebouncedSearch] = useState(search)

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => setDebouncedSearch(search), 350)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [search])

  const buildParams = useCallback(() => {
    const p = new URLSearchParams()
    if (debouncedSearch) p.set('search', debouncedSearch)
    if (severity) p.set('severity', severity)
    if (status) p.set('status', status)
    if (category) p.set('category', category)
    if (nis2) p.set('nis2', 'true')
    if (dateFrom) p.set('dateFrom', dateFrom)
    if (dateTo) p.set('dateTo', dateTo)
    if (sortBy !== 'createdAt') p.set('sortBy', sortBy)
    if (sortDir !== 'desc') p.set('sortDir', sortDir)
    if (page > 1) p.set('page', String(page))
    return p
  }, [debouncedSearch, severity, status, category, nis2, dateFrom, dateTo, sortBy, sortDir, page])

  // Sync URL
  useEffect(() => {
    const p = buildParams()
    router.replace(`/incidents${p.toString() ? '?' + p.toString() : ''}`, { scroll: false })
  }, [buildParams, router])

  const fetchIncidents = useCallback(async () => {
    setLoading(true)
    const p = buildParams()
    p.set('limit', '25')
    const res = await fetch(`/api/incidents?${p}`)
    if (res.ok) {
      const json = await res.json()
      setResult(json)
    }
    setLoading(false)
  }, [buildParams])

  useEffect(() => { fetchIncidents() }, [fetchIncidents])

  function handleSort(field: SortField) {
    if (field === sortBy) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
    setPage(1)
  }

  function resetFilters() {
    setSearch(''); setSeverity(''); setStatus(''); setCategory('')
    setNis2(false); setDateFrom(''); setDateTo('')
    setSortBy('createdAt'); setSortDir('desc'); setPage(1)
  }

  const hasFilters = !!(search || severity || status || category || nis2 || dateFrom || dateTo)
  const incidents = result?.data || []

  const thStyle = (field: SortField): React.CSSProperties => ({
    padding: '10px 16px',
    textAlign: 'left',
    fontSize: '11px',
    color: sortBy === field ? '#93c5fd' : '#555b6e',
    fontFamily: 'IBM Plex Mono, monospace',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontWeight: 500,
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  })

  const selStyle: React.CSSProperties = {
    padding: '7px 10px',
    background: '#161922',
    border: '1px solid rgba(255,255,255,0.07)',
    borderRadius: '6px',
    color: '#8b90a0',
    fontSize: '12px',
    outline: 'none',
  }

  return (
    <div style={{ padding: '24px', flex: 1, minWidth: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Incydenty</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>
            Zarządzanie incydentami bezpieczeństwa informacji
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <a
            href={`/api/incidents/export?${buildParams()}`}
            download
            style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', fontSize: '13px', color: '#8b90a0', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            CSV
          </a>
          <button
            onClick={() => setShowForm(true)}
            style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}
          >
            + Nowy incydent
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
        {[
          { label: 'Otwarte', value: result?.stats.open ?? '—', color: '#ef4444' },
          { label: 'NIS2 aktywny', value: result ? incidents.filter(i => i.nis2Active).length : '—', color: '#f59e0b' },
          { label: 'Zamknięte', value: result?.stats.closed ?? '—', color: '#22c55e' },
          { label: 'Wyników (filtr)', value: result?.total ?? '—', color: '#3b82f6' },
        ].map((s) => (
          <div key={s.label} style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
            <div style={{ fontSize: '28px', fontWeight: 600, color: s.color, fontFamily: 'IBM Plex Mono, monospace' }}>{s.value}</div>
            <div style={{ fontSize: '12px', color: '#8b90a0', marginTop: '4px' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Szukaj (tytuł, nr, zgłaszający)..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          style={{ flex: '1', minWidth: '200px', padding: '7px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none' }}
        />
        <select value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1) }} style={selStyle}>
          <option value="">Wszystkie poziomy</option>
          <option value="CRITICAL">Krytyczny</option>
          <option value="HIGH">Wysoki</option>
          <option value="MEDIUM">Średni</option>
          <option value="LOW">Niski</option>
        </select>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }} style={selStyle}>
          <option value="">Wszystkie statusy</option>
          <option value="NEW">Nowy</option>
          <option value="IN_PROGRESS">W toku</option>
          <option value="ANALYSIS">Analiza</option>
          <option value="CLOSED">Zamknięty</option>
        </select>
        <select value={category} onChange={(e) => { setCategory(e.target.value); setPage(1) }} style={selStyle}>
          <option value="">Wszystkie kategorie</option>
          <option value="UNAUTHORIZED_ACCESS">Nieautoryzowany dostęp</option>
          <option value="DATA_LEAK">Wyciek danych</option>
          <option value="AVAILABILITY">Niedostępność</option>
          <option value="PHISHING">Phishing</option>
          <option value="MALWARE">Złośliwe oprog.</option>
          <option value="PHYSICAL">Fizyczny</option>
          <option value="OTHER">Inne</option>
        </select>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', padding: '7px 10px', border: nis2 ? '1px solid rgba(245,158,11,0.4)' : '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', background: nis2 ? 'rgba(245,158,11,0.1)' : '#161922', fontSize: '12px', color: nis2 ? '#fcd34d' : '#8b90a0', userSelect: 'none' }}>
          <input type="checkbox" checked={nis2} onChange={(e) => { setNis2(e.target.checked); setPage(1) }} style={{ accentColor: '#f59e0b' }} />
          NIS2
        </label>
      </div>

      {/* Date range + reset */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', color: '#555b6e' }}>Od:</span>
          <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1) }} style={{ ...selStyle, colorScheme: 'dark' }} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', color: '#555b6e' }}>Do:</span>
          <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1) }} style={{ ...selStyle, colorScheme: 'dark' }} />
        </div>
        {hasFilters && (
          <button onClick={resetFilters} style={{ marginLeft: 'auto', padding: '6px 12px', background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px', cursor: 'pointer' }}>
            ✕ Wyczyść filtry
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <th onClick={() => handleSort('incidentNumber')} style={thStyle('incidentNumber')}>
                Nr <SortIcon field="incidentNumber" current={sortBy} dir={sortDir} />
              </th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                Incydent
              </th>
              <th onClick={() => handleSort('severity')} style={thStyle('severity')}>
                Poziom <SortIcon field="severity" current={sortBy} dir={sortDir} />
              </th>
              <th onClick={() => handleSort('status')} style={thStyle('status')}>
                Status <SortIcon field="status" current={sortBy} dir={sortDir} />
              </th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                NIS2
              </th>
              <th onClick={() => handleSort('createdAt')} style={thStyle('createdAt')}>
                Data <SortIcon field="createdAt" current={sortBy} dir={sortDir} />
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Ładowanie...</td></tr>
            ) : incidents.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Brak incydentów spełniających kryteria</td></tr>
            ) : incidents.map((incident) => {
              const sc = SEV_COLORS[incident.severity] || SEV_COLORS.LOW
              const stc = ST_COLORS[incident.status] || ST_COLORS.NEW
              return (
                <tr key={incident.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', cursor: 'pointer' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
                  <td style={{ padding: '12px 16px' }}>
                    <Link href={`/incidents/${incident.id}`} style={{ textDecoration: 'none' }}>
                      <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>{incident.incidentNumber}</span>
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px', maxWidth: '320px' }}>
                    <Link href={`/incidents/${incident.id}`} style={{ textDecoration: 'none' }}>
                      <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500, marginBottom: '3px' }}>{incident.title}</div>
                      <div style={{ fontSize: '11px', color: '#555b6e' }}>
                        {CATEGORY_LABELS[incident.category]} · zgł. {incident.reportedBy}
                        {incident._count.evidences > 0 && ` · ${incident._count.evidences} dow.`}
                      </div>
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: sc.bg, color: sc.text, border: `1px solid ${sc.border}` }}>
                      {SEVERITY_LABELS[incident.severity]}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: stc.bg, color: stc.text, border: `1px solid ${stc.border}` }}>
                      {STATUS_LABELS[incident.status]}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {incident.nis2Active
                      ? <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: 'rgba(245,158,11,0.15)', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.25)' }}>NIS2</span>
                      : <span style={{ color: '#3a3f52', fontSize: '11px' }}>—</span>}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap' }}>
                    {formatDate(incident.createdAt)}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {result && result.pages > 1 && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '16px' }}>
          <span style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
            Strona {result.page} z {result.pages} · {result.total} wyników
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page <= 1 ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page <= 1 ? 'default' : 'pointer' }}
            >
              ← Poprzednia
            </button>
            {Array.from({ length: Math.min(result.pages, 7) }, (_, i) => {
              const p = result.pages <= 7 ? i + 1 : page <= 4 ? i + 1 : page >= result.pages - 3 ? result.pages - 6 + i : page - 3 + i
              return (
                <button key={p} onClick={() => setPage(p)}
                  style={{ padding: '6px 10px', borderRadius: '6px', fontSize: '12px', border: p === page ? '1px solid rgba(59,130,246,0.4)' : '1px solid rgba(255,255,255,0.07)', background: p === page ? 'rgba(59,130,246,0.1)' : '#161922', color: p === page ? '#93c5fd' : '#8b90a0', cursor: 'pointer', fontFamily: 'IBM Plex Mono, monospace' }}>
                  {p}
                </button>
              )
            })}
            <button
              disabled={page >= result.pages}
              onClick={() => setPage(p => p + 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page >= result.pages ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page >= result.pages ? 'default' : 'pointer' }}
            >
              Następna →
            </button>
          </div>
        </div>
      )}
      {result && result.total > 0 && result.pages <= 1 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'right' }}>
          {result.total} wyników
        </div>
      )}

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

  const iStyle: React.CSSProperties = { width: '100%', padding: '8px 12px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }
  const F = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', marginBottom: '6px', fontFamily: 'IBM Plex Mono, monospace' }}>{label}</label>
      {children}
    </div>
  )

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '32px', width: '540px', maxWidth: '95vw' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#e8eaf0', marginBottom: '24px' }}>Nowy incydent bezpieczeństwa</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <F label="Tytuł incydentu">
              <input required minLength={3} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Krótki opis zdarzenia..." style={iStyle} />
            </F>
            <F label="Opis zdarzenia">
              <textarea required minLength={10} rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Szczegółowy opis incydentu..." style={{ ...iStyle, resize: 'vertical' }} />
            </F>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <F label="Klasyfikacja">
                <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} style={iStyle}>
                  <option value="CRITICAL">Krytyczny</option>
                  <option value="HIGH">Wysoki</option>
                  <option value="MEDIUM">Średni</option>
                  <option value="LOW">Niski</option>
                </select>
              </F>
              <F label="Kategoria">
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} style={iStyle}>
                  <option value="UNAUTHORIZED_ACCESS">Nieautoryzowany dostęp</option>
                  <option value="DATA_LEAK">Wyciek danych</option>
                  <option value="AVAILABILITY">Niedostępność</option>
                  <option value="PHISHING">Phishing</option>
                  <option value="MALWARE">Złośliwe oprogramowanie</option>
                  <option value="PHYSICAL">Incydent fizyczny</option>
                  <option value="OTHER">Inne</option>
                </select>
              </F>
            </div>
            <F label="Zgłaszający">
              <input required value={form.reportedBy} onChange={(e) => setForm({ ...form, reportedBy: e.target.value })} placeholder="Imię i nazwisko zgłaszającego" style={iStyle} />
            </F>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={form.nis2Active} onChange={(e) => setForm({ ...form, nis2Active: e.target.checked })} />
              <span style={{ fontSize: '13px', color: '#8b90a0' }}>Incydent podlega raportowaniu NIS2 (Art. 21)</span>
            </label>
          </div>
          {error && (
            <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>{error}</div>
          )}
          <div style={{ display: 'flex', gap: '8px', marginTop: '24px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={{ padding: '8px 16px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>Anuluj</button>
            <button type="submit" disabled={loading} style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Tworzenie...' : 'Utwórz incydent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
