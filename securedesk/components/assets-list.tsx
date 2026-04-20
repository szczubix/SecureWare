'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { formatDateShort, ASSET_TYPE_LABELS, CLASSIFICATION_LABELS } from '@/lib/utils'

interface Asset {
  id: string
  assetNumber: string
  name: string
  type: string
  classification: string
  description: string | null
  location: string | null
  businessOwner: string | null
  technicalOwner: string | null
  nextReviewAt: string | null
  createdAt: string
  _count: { incidents: number }
}

interface PagedResponse {
  data: Asset[]
  total: number
  page: number
  pages: number
  stats: { total: number; restricted: number; noOwner: number; overdueReview: number }
}

const CC: Record<string, { bg: string; text: string; border: string }> = {
  RESTRICTED: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  CONFIDENTIAL: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  INTERNAL: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  PUBLIC: { bg: 'rgba(34,197,94,0.15)', text: '#86efac', border: 'rgba(34,197,94,0.25)' },
}

type SortField = 'createdAt' | 'name' | 'type' | 'classification' | 'nextReviewAt' | 'assetNumber'

function SortIcon({ field, current, dir }: { field: string; current: string; dir: string }) {
  if (field !== current) return <span style={{ color: '#3a3f52', marginLeft: '4px' }}>↕</span>
  return <span style={{ color: '#3b82f6', marginLeft: '4px' }}>{dir === 'asc' ? '↑' : '↓'}</span>
}

export function AssetsList() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [result, setResult] = useState<PagedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [filterType, setFilterType] = useState(searchParams.get('type') || '')
  const [filterClass, setFilterClass] = useState(searchParams.get('classification') || '')
  const [noOwner, setNoOwner] = useState(searchParams.get('noOwner') === 'true')
  const [overdue, setOverdue] = useState(searchParams.get('overdueReview') === 'true')
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
    if (filterType) p.set('type', filterType)
    if (filterClass) p.set('classification', filterClass)
    if (noOwner) p.set('noOwner', 'true')
    if (overdue) p.set('overdueReview', 'true')
    if (sortBy !== 'createdAt') p.set('sortBy', sortBy)
    if (sortDir !== 'desc') p.set('sortDir', sortDir)
    if (page > 1) p.set('page', String(page))
    return p
  }, [debouncedSearch, filterType, filterClass, noOwner, overdue, sortBy, sortDir, page])

  useEffect(() => {
    const p = buildParams()
    router.replace(`/assets${p.toString() ? '?' + p.toString() : ''}`, { scroll: false })
  }, [buildParams, router])

  const fetchAssets = useCallback(async () => {
    setLoading(true)
    const p = buildParams()
    p.set('limit', '25')
    const res = await fetch(`/api/assets?${p}`)
    if (res.ok) {
      const json = await res.json()
      setResult(json)
    }
    setLoading(false)
  }, [buildParams])

  useEffect(() => { fetchAssets() }, [fetchAssets])

  function handleSort(field: SortField) {
    if (field === sortBy) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortDir('asc')
    }
    setPage(1)
  }

  function resetFilters() {
    setSearch(''); setFilterType(''); setFilterClass('')
    setNoOwner(false); setOverdue(false)
    setSortBy('createdAt'); setSortDir('desc'); setPage(1)
  }

  const hasFilters = !!(search || filterType || filterClass || noOwner || overdue)
  const assets = result?.data || []

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

  const toggleStyle = (active: boolean): React.CSSProperties => ({
    display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer',
    padding: '7px 10px',
    border: active ? '1px solid rgba(245,158,11,0.4)' : '1px solid rgba(255,255,255,0.07)',
    borderRadius: '6px',
    background: active ? 'rgba(245,158,11,0.1)' : '#161922',
    fontSize: '12px',
    color: active ? '#fcd34d' : '#8b90a0',
    userSelect: 'none',
  })

  return (
    <div style={{ padding: '24px', flex: 1, minWidth: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Aktywa</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>Rejestr aktywów informacyjnych organizacji</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <a
            href={`/api/assets/export?${buildParams()}`}
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
            + Nowe aktywo
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
        {[
          { label: 'Aktywów łącznie', value: result?.stats.total ?? '—', color: '#e8eaf0' },
          { label: 'Restricted', value: result?.stats.restricted ?? '—', color: '#fca5a5' },
          { label: 'Bez właściciela', value: result?.stats.noOwner ?? '—', color: '#fcd34d' },
          { label: 'Przegląd przeterminowany', value: result?.stats.overdueReview ?? '—', color: '#fcd34d' },
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
          placeholder="Szukaj (nazwa, nr, lokalizacja, właściciel)..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          style={{ flex: '1', minWidth: '220px', padding: '7px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none' }}
        />
        <select value={filterType} onChange={(e) => { setFilterType(e.target.value); setPage(1) }} style={selStyle}>
          <option value="">Wszystkie typy</option>
          <option value="HARDWARE">Sprzęt</option>
          <option value="SOFTWARE">Oprogramowanie</option>
          <option value="DATA">Dane</option>
          <option value="CLOUD_SERVICE">Usługa cloud</option>
          <option value="INFRASTRUCTURE">Infrastruktura</option>
          <option value="OTHER">Inne</option>
        </select>
        <select value={filterClass} onChange={(e) => { setFilterClass(e.target.value); setPage(1) }} style={selStyle}>
          <option value="">Wszystkie klasy</option>
          <option value="RESTRICTED">Zastrzeżony</option>
          <option value="CONFIDENTIAL">Poufny</option>
          <option value="INTERNAL">Wewnętrzny</option>
          <option value="PUBLIC">Publiczny</option>
        </select>
        <label style={toggleStyle(overdue)}>
          <input type="checkbox" checked={overdue} onChange={(e) => { setOverdue(e.target.checked); setPage(1) }} style={{ accentColor: '#f59e0b' }} />
          Przegląd przeterminowany
        </label>
        <label style={toggleStyle(noOwner)}>
          <input type="checkbox" checked={noOwner} onChange={(e) => { setNoOwner(e.target.checked); setPage(1) }} style={{ accentColor: '#f59e0b' }} />
          Bez właściciela
        </label>
        {hasFilters && (
          <button onClick={resetFilters} style={{ padding: '6px 12px', background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px', cursor: 'pointer' }}>
            ✕ Wyczyść
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <th onClick={() => handleSort('assetNumber')} style={thStyle('assetNumber')}>
                Nr <SortIcon field="assetNumber" current={sortBy} dir={sortDir} />
              </th>
              <th onClick={() => handleSort('name')} style={thStyle('name')}>
                Aktywo <SortIcon field="name" current={sortBy} dir={sortDir} />
              </th>
              <th onClick={() => handleSort('type')} style={thStyle('type')}>
                Typ <SortIcon field="type" current={sortBy} dir={sortDir} />
              </th>
              <th onClick={() => handleSort('classification')} style={thStyle('classification')}>
                Klasyfikacja <SortIcon field="classification" current={sortBy} dir={sortDir} />
              </th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                Właściciel
              </th>
              <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                Incydenty
              </th>
              <th onClick={() => handleSort('nextReviewAt')} style={thStyle('nextReviewAt')}>
                Przegląd <SortIcon field="nextReviewAt" current={sortBy} dir={sortDir} />
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Ładowanie...</td></tr>
            ) : assets.length === 0 ? (
              <tr><td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Brak aktywów spełniających kryteria</td></tr>
            ) : assets.map((asset) => {
              const cc = CC[asset.classification] || CC.INTERNAL
              const isOverdue = asset.nextReviewAt && new Date(asset.nextReviewAt) < new Date()
              return (
                <tr key={asset.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
                  <td style={{ padding: '12px 16px' }}>
                    <Link href={`/assets/${asset.id}`} style={{ textDecoration: 'none' }}>
                      <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>{asset.assetNumber}</span>
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px', maxWidth: '280px' }}>
                    <Link href={`/assets/${asset.id}`} style={{ textDecoration: 'none' }}>
                      <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500, marginBottom: '2px' }}>{asset.name}</div>
                      {asset.location && <div style={{ fontSize: '11px', color: '#555b6e' }}>{asset.location}</div>}
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontSize: '12px', color: '#8b90a0' }}>{ASSET_TYPE_LABELS[asset.type]}</span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: cc.bg, color: cc.text, border: `1px solid ${cc.border}` }}>
                      {CLASSIFICATION_LABELS[asset.classification]}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <div style={{ fontSize: '12px', color: '#8b90a0' }}>
                      {asset.businessOwner || asset.technicalOwner || <span style={{ color: '#f59e0b', fontSize: '11px' }}>Brak właściciela</span>}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {asset._count.incidents > 0
                      ? <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: 'rgba(239,68,68,0.1)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>{asset._count.incidents}</span>
                      : <span style={{ color: '#3a3f52', fontSize: '12px' }}>—</span>}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {asset.nextReviewAt
                      ? <span style={{ fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', color: isOverdue ? '#fca5a5' : '#555b6e', whiteSpace: 'nowrap' }}>
                          {isOverdue ? '⚠ ' : ''}{formatDateShort(asset.nextReviewAt)}
                        </span>
                      : <span style={{ color: '#3a3f52', fontSize: '12px' }}>—</span>}
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
            Strona {result.page} z {result.pages} · {result.total} aktywów
          </span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page <= 1 ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page <= 1 ? 'default' : 'pointer' }}>
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
            <button disabled={page >= result.pages} onClick={() => setPage(p => p + 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page >= result.pages ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page >= result.pages ? 'default' : 'pointer' }}>
              Następna →
            </button>
          </div>
        </div>
      )}
      {result && result.total > 0 && result.pages <= 1 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'right' }}>
          {result.total} aktywów
        </div>
      )}

      {showForm && (
        <NewAssetModal
          onClose={() => setShowForm(false)}
          onCreated={() => { setShowForm(false); fetchAssets() }}
        />
      )}
    </div>
  )
}

function NewAssetModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({ name: '', type: 'HARDWARE', classification: 'INTERNAL', description: '', location: '', businessOwner: '', technicalOwner: '' })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const res = await fetch('/api/assets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
    if (res.ok) { onCreated() }
    else {
      const data = await res.json()
      setError(data.error?.formErrors?.[0] || 'Błąd podczas tworzenia aktywa')
      setLoading(false)
    }
  }

  const iStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }
  const F = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', marginBottom: '5px', fontFamily: 'IBM Plex Mono, monospace' }}>{label}</label>
      {children}
    </div>
  )

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '32px', width: '520px', maxWidth: '95vw' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#e8eaf0', marginBottom: '24px' }}>Nowe aktywo</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <F label="Nazwa aktywa"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nazwa zasobu informacyjnego" style={iStyle} /></F>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <F label="Typ">
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} style={iStyle}>
                  <option value="HARDWARE">Sprzęt</option>
                  <option value="SOFTWARE">Oprogramowanie</option>
                  <option value="DATA">Dane</option>
                  <option value="CLOUD_SERVICE">Usługa cloud</option>
                  <option value="INFRASTRUCTURE">Infrastruktura</option>
                  <option value="OTHER">Inne</option>
                </select>
              </F>
              <F label="Klasyfikacja">
                <select value={form.classification} onChange={(e) => setForm({ ...form, classification: e.target.value })} style={iStyle}>
                  <option value="PUBLIC">Publiczny</option>
                  <option value="INTERNAL">Wewnętrzny</option>
                  <option value="CONFIDENTIAL">Poufny</option>
                  <option value="RESTRICTED">Zastrzeżony</option>
                </select>
              </F>
            </div>
            <F label="Lokalizacja"><input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Np. serwerownia, chmura AWS" style={iStyle} /></F>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <F label="Właściciel biznesowy"><input value={form.businessOwner} onChange={(e) => setForm({ ...form, businessOwner: e.target.value })} placeholder="Imię i nazwisko" style={iStyle} /></F>
              <F label="Właściciel techniczny"><input value={form.technicalOwner} onChange={(e) => setForm({ ...form, technicalOwner: e.target.value })} placeholder="Imię i nazwisko" style={iStyle} /></F>
            </div>
            <F label="Opis"><textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Opis aktywa..." style={{ ...iStyle, resize: 'vertical' }} /></F>
          </div>
          {error && <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>{error}</div>}
          <div style={{ display: 'flex', gap: '8px', marginTop: '20px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>Anuluj</button>
            <button type="submit" disabled={loading} style={{ padding: '8px 14px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Tworzenie...' : 'Utwórz aktywo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
