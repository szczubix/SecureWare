'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { formatDateShort } from '@/lib/utils'

interface Asset { id: string; assetNumber: string; name: string }
interface Risk {
  id: string
  riskNumber: string
  title: string
  description: string
  category: string
  probability: number
  impact: number
  riskScore: number
  treatment: string
  status: string
  owner: string
  residualScore: number | null
  nextReviewAt: string | null
  createdAt: string
  assets: { asset: Asset }[]
}

interface PagedResponse {
  data: Risk[]
  total: number
  page: number
  pages: number
  stats: { total: number; open: number; high: number; overdue: number }
}

const CATEGORY_PL: Record<string, string> = {
  CONFIDENTIALITY: 'Poufność', INTEGRITY: 'Integralność', AVAILABILITY: 'Dostępność',
  PHYSICAL: 'Fizyczne', LEGAL: 'Prawne', OTHER: 'Inne',
}
const TREATMENT_PL: Record<string, string> = {
  ACCEPT: 'Akceptacja', MITIGATE: 'Mitigacja', TRANSFER: 'Transfer', AVOID: 'Unikanie',
}
const STATUS_PL: Record<string, string> = {
  OPEN: 'Otwarte', IN_TREATMENT: 'W trakcie', ACCEPTED: 'Zaakceptowane', CLOSED: 'Zamknięte',
}

function scoreLevel(s: number): { label: string; color: string; bg: string; border: string } {
  if (s >= 15) return { label: 'Krytyczne', color: '#fca5a5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)' }
  if (s >= 10) return { label: 'Wysokie',   color: '#fdba74', bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.3)' }
  if (s >= 5)  return { label: 'Średnie',   color: '#fcd34d', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)' }
  return             { label: 'Niskie',    color: '#86efac', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.3)' }
}

function cellColor(p: number, i: number): string {
  const s = p * i
  if (s >= 15) return 'rgba(239,68,68,0.35)'
  if (s >= 10) return 'rgba(249,115,22,0.3)'
  if (s >= 5)  return 'rgba(245,158,11,0.25)'
  return 'rgba(34,197,94,0.15)'
}

function RiskMatrix({ risks }: { risks: Risk[] }) {
  return (
    <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '10px', padding: '16px' }}>
      <div style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '10px' }}>
        MACIERZ RYZYK (Prawdopodobieństwo × Wpływ)
      </div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        {/* Y-axis label */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '150px', paddingBottom: '18px' }}>
          {[5,4,3,2,1].map(p => (
            <div key={p} style={{ fontSize: '10px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'right', lineHeight: '28px' }}>{p}</div>
          ))}
        </div>
        <div>
          {/* Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,28px)', gridTemplateRows: 'repeat(5,28px)', gap: '2px' }}>
            {[5,4,3,2,1].map(p =>
              [1,2,3,4,5].map(i => {
                const dotsHere = risks.filter(r => r.probability === p && r.impact === i)
                return (
                  <div key={`${p}-${i}`} title={dotsHere.map(r => r.riskNumber).join(', ')}
                    style={{ background: cellColor(p, i), borderRadius: '3px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', cursor: dotsHere.length > 0 ? 'pointer' : 'default' }}>
                    {dotsHere.length > 0 && (
                      <span style={{ fontSize: '9px', fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Mono, monospace' }}>
                        {dotsHere.length}
                      </span>
                    )}
                  </div>
                )
              })
            )}
          </div>
          {/* X-axis labels */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,28px)', gap: '2px', marginTop: '4px' }}>
            {[1,2,3,4,5].map(i => (
              <div key={i} style={{ fontSize: '10px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'center' }}>{i}</div>
            ))}
          </div>
        </div>
        {/* Legend */}
        <div style={{ paddingBottom: '20px', marginLeft: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {[
            { label: 'Krytyczne ≥15', color: 'rgba(239,68,68,0.5)' },
            { label: 'Wysokie 10-14', color: 'rgba(249,115,22,0.45)' },
            { label: 'Średnie 5-9',   color: 'rgba(245,158,11,0.4)' },
            { label: 'Niskie 1-4',    color: 'rgba(34,197,94,0.35)' },
          ].map(l => (
            <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '2px', background: l.color, flexShrink: 0 }} />
              <span style={{ fontSize: '10px', color: '#555b6e', whiteSpace: 'nowrap' }}>{l.label}</span>
            </div>
          ))}
          <div style={{ fontSize: '10px', color: '#3a3f52', marginTop: '2px' }}>P↑ / W→</div>
        </div>
      </div>
    </div>
  )
}

type SortField = 'riskScore' | 'residualScore' | 'createdAt' | 'status' | 'riskNumber'

function SortIcon({ field, current, dir }: { field: string; current: string; dir: string }) {
  if (field !== current) return <span style={{ color: '#3a3f52', marginLeft: '4px' }}>↕</span>
  return <span style={{ color: '#3b82f6', marginLeft: '4px' }}>{dir === 'asc' ? '↑' : '↓'}</span>
}

export function RisksList() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const [result, setResult] = useState<PagedResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const [search, setSearch]         = useState(searchParams.get('search') || '')
  const [status, setStatus]         = useState(searchParams.get('status') || '')
  const [category, setCategory]     = useState(searchParams.get('category') || '')
  const [treatment, setTreatment]   = useState(searchParams.get('treatment') || '')
  const [minScore, setMinScore]     = useState(searchParams.get('minScore') || '')
  const [sortBy, setSortBy]         = useState<SortField>((searchParams.get('sortBy') as SortField) || 'riskScore')
  const [sortDir, setSortDir]       = useState<'asc'|'desc'>(searchParams.get('sortDir') === 'asc' ? 'asc' : 'desc')
  const [page, setPage]             = useState(parseInt(searchParams.get('page') || '1', 10))

  const debRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [debSearch, setDebSearch] = useState(search)
  useEffect(() => {
    if (debRef.current) clearTimeout(debRef.current)
    debRef.current = setTimeout(() => setDebSearch(search), 350)
    return () => { if (debRef.current) clearTimeout(debRef.current) }
  }, [search])

  const buildParams = useCallback(() => {
    const p = new URLSearchParams()
    if (debSearch)  p.set('search', debSearch)
    if (status)     p.set('status', status)
    if (category)   p.set('category', category)
    if (treatment)  p.set('treatment', treatment)
    if (minScore)   p.set('minScore', minScore)
    if (sortBy !== 'riskScore') p.set('sortBy', sortBy)
    if (sortDir !== 'desc') p.set('sortDir', sortDir)
    if (page > 1)   p.set('page', String(page))
    return p
  }, [debSearch, status, category, treatment, minScore, sortBy, sortDir, page])

  useEffect(() => {
    const p = buildParams()
    router.replace(`/risks${p.toString() ? '?' + p.toString() : ''}`, { scroll: false })
  }, [buildParams, router])

  const fetchRisks = useCallback(async () => {
    setLoading(true)
    const p = buildParams()
    p.set('limit', '25')
    const res = await fetch(`/api/risks?${p}`)
    if (res.ok) setResult(await res.json())
    setLoading(false)
  }, [buildParams])

  useEffect(() => { fetchRisks() }, [fetchRisks])

  function handleSort(field: SortField) {
    if (field === sortBy) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortBy(field); setSortDir('desc') }
    setPage(1)
  }

  function reset() {
    setSearch(''); setStatus(''); setCategory(''); setTreatment(''); setMinScore('')
    setSortBy('riskScore'); setSortDir('desc'); setPage(1)
  }

  const hasFilters = !!(search || status || category || treatment || minScore)
  const risks = result?.data || []

  const sel: React.CSSProperties = { padding: '7px 10px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px', outline: 'none' }
  const th = (f: SortField): React.CSSProperties => ({
    padding: '10px 16px', textAlign: 'left', fontSize: '11px',
    color: sortBy === f ? '#93c5fd' : '#555b6e',
    fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase',
    letterSpacing: '0.05em', fontWeight: 500, cursor: 'pointer', userSelect: 'none', whiteSpace: 'nowrap',
  })
  const thPlain: React.CSSProperties = { padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }

  return (
    <div style={{ padding: '24px', flex: 1, minWidth: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Rejestr ryzyk</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>ISO 27001:2022 · Ocena i postępowanie z ryzykiem</p>
        </div>
        <button onClick={() => setShowForm(true)}
          style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}>
          + Nowe ryzyko
        </button>
      </div>

      {/* Stats + Matrix */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '16px', marginBottom: '24px', alignItems: 'start' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: '12px' }}>
          {[
            { label: 'Wszystkich', value: result?.stats.total ?? '—', color: '#e8eaf0' },
            { label: 'Otwarte / W trakcie', value: result?.stats.open ?? '—', color: '#f59e0b' },
            { label: 'Krytyczne (≥15)', value: result?.stats.high ?? '—', color: '#ef4444' },
            { label: 'Przegląd przeterminowany', value: result?.stats.overdue ?? '—', color: '#fcd34d' },
          ].map(s => (
            <div key={s.label} style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '14px 16px' }}>
              <div style={{ fontSize: '26px', fontWeight: 600, color: s.color, fontFamily: 'IBM Plex Mono, monospace' }}>{s.value}</div>
              <div style={{ fontSize: '11px', color: '#8b90a0', marginTop: '4px' }}>{s.label}</div>
            </div>
          ))}
        </div>
        <RiskMatrix risks={risks} />
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input type="text" placeholder="Szukaj (tytuł, nr, właściciel, zagrożenie)..."
          value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
          style={{ flex: '1', minWidth: '220px', padding: '7px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none' }} />
        <select value={status} onChange={e => { setStatus(e.target.value); setPage(1) }} style={sel}>
          <option value="">Wszystkie statusy</option>
          <option value="OPEN">Otwarte</option>
          <option value="IN_TREATMENT">W trakcie</option>
          <option value="ACCEPTED">Zaakceptowane</option>
          <option value="CLOSED">Zamknięte</option>
        </select>
        <select value={category} onChange={e => { setCategory(e.target.value); setPage(1) }} style={sel}>
          <option value="">Wszystkie kategorie</option>
          <option value="CONFIDENTIALITY">Poufność</option>
          <option value="INTEGRITY">Integralność</option>
          <option value="AVAILABILITY">Dostępność</option>
          <option value="PHYSICAL">Fizyczne</option>
          <option value="LEGAL">Prawne</option>
          <option value="OTHER">Inne</option>
        </select>
        <select value={treatment} onChange={e => { setTreatment(e.target.value); setPage(1) }} style={sel}>
          <option value="">Wszystkie podejścia</option>
          <option value="MITIGATE">Mitigacja</option>
          <option value="ACCEPT">Akceptacja</option>
          <option value="TRANSFER">Transfer</option>
          <option value="AVOID">Unikanie</option>
        </select>
        <select value={minScore} onChange={e => { setMinScore(e.target.value); setPage(1) }} style={sel}>
          <option value="">Wszystkie poziomy</option>
          <option value="15">Krytyczne (≥15)</option>
          <option value="10">Wysokie+ (≥10)</option>
          <option value="5">Średnie+ (≥5)</option>
        </select>
        {hasFilters && (
          <button onClick={reset} style={{ padding: '6px 12px', background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px', cursor: 'pointer' }}>
            ✕ Wyczyść
          </button>
        )}
      </div>

      {/* Table */}
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              <th onClick={() => handleSort('riskNumber')} style={th('riskNumber')}>Nr <SortIcon field="riskNumber" current={sortBy} dir={sortDir}/></th>
              <th style={thPlain}>Ryzyko</th>
              <th style={thPlain}>Kategoria</th>
              <th onClick={() => handleSort('riskScore')} style={th('riskScore')}>P×W <SortIcon field="riskScore" current={sortBy} dir={sortDir}/></th>
              <th onClick={() => handleSort('residualScore')} style={th('residualScore')}>Rezydualne <SortIcon field="residualScore" current={sortBy} dir={sortDir}/></th>
              <th style={thPlain}>Podejście</th>
              <th onClick={() => handleSort('status')} style={th('status')}>Status <SortIcon field="status" current={sortBy} dir={sortDir}/></th>
              <th style={thPlain}>Właściciel</th>
              <th onClick={() => handleSort('createdAt')} style={th('createdAt')}>Data <SortIcon field="createdAt" current={sortBy} dir={sortDir}/></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Ładowanie...</td></tr>
            ) : risks.length === 0 ? (
              <tr><td colSpan={9} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Brak ryzyk spełniających kryteria</td></tr>
            ) : risks.map(risk => {
              const lvl = scoreLevel(risk.riskScore)
              const resLvl = risk.residualScore !== null ? scoreLevel(risk.residualScore) : null
              const overdue = risk.nextReviewAt && new Date(risk.nextReviewAt) < new Date()
              return (
                <tr key={risk.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                  <td style={{ padding: '12px 16px' }}>
                    <Link href={`/risks/${risk.id}`} style={{ textDecoration: 'none', fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>
                      {risk.riskNumber}
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px', maxWidth: '280px' }}>
                    <Link href={`/risks/${risk.id}`} style={{ textDecoration: 'none' }}>
                      <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500, marginBottom: '2px' }}>{risk.title}</div>
                      {risk.assets.length > 0 && (
                        <div style={{ fontSize: '11px', color: '#555b6e' }}>{risk.assets.map(a => a.asset.assetNumber).join(', ')}</div>
                      )}
                    </Link>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#8b90a0' }}>{CATEGORY_PL[risk.category] || risk.category}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 10px', borderRadius: '4px', fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, background: lvl.bg, color: lvl.color, border: `1px solid ${lvl.border}` }}>
                      {risk.riskScore}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {resLvl ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '2px 10px', borderRadius: '4px', fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, background: resLvl.bg, color: resLvl.color, border: `1px solid ${resLvl.border}` }}>
                        {risk.residualScore}
                      </span>
                    ) : <span style={{ color: '#3a3f52', fontSize: '12px' }}>—</span>}
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#8b90a0' }}>{TREATMENT_PL[risk.treatment] || risk.treatment}</td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{ fontSize: '11px', color: '#8b90a0' }}>{STATUS_PL[risk.status] || risk.status}</span>
                  </td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#8b90a0', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{risk.owner}</td>
                  <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap' }}>
                    {overdue && <span style={{ color: '#fca5a5', marginRight: '4px' }}>⚠</span>}
                    {formatDateShort(risk.createdAt)}
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
          <span style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>Strona {result.page} z {result.pages} · {result.total} ryzyk</span>
          <div style={{ display: 'flex', gap: '6px' }}>
            <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page <= 1 ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page <= 1 ? 'default' : 'pointer' }}>← Poprzednia</button>
            <button disabled={page >= result.pages} onClick={() => setPage(p => p + 1)}
              style={{ padding: '6px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: page >= result.pages ? '#3a3f52' : '#8b90a0', fontSize: '12px', cursor: page >= result.pages ? 'default' : 'pointer' }}>Następna →</button>
          </div>
        </div>
      )}
      {result && result.total > 0 && result.pages <= 1 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'right' }}>{result.total} ryzyk</div>
      )}

      {showForm && <NewRiskModal onClose={() => setShowForm(false)} onCreated={() => { setShowForm(false); fetchRisks() }} />}
    </div>
  )
}

function NewRiskModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [prob, setProb] = useState(3)
  const [impact, setImpact] = useState(3)
  const [form, setForm] = useState({
    title: '', description: '', threat: '', vulnerability: '',
    category: 'OTHER', treatment: 'MITIGATE', owner: '',
    mitigationPlan: '',
  })

  const score = prob * impact
  const lvl = scoreLevel(score)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError('')
    const res = await fetch('/api/risks', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, probability: prob, impact }),
    })
    if (res.ok) { onCreated() }
    else {
      const d = await res.json()
      setError(d.error?.formErrors?.[0] || 'Błąd podczas tworzenia')
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
  const ScaleBtn = ({ val, current, set }: { val: number; current: number; set: (v: number) => void }) => (
    <button type="button" onClick={() => set(val)} style={{ width: '32px', height: '32px', borderRadius: '6px', border: current === val ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)', background: current === val ? 'rgba(59,130,246,0.2)' : '#0f1117', color: current === val ? '#93c5fd' : '#555b6e', fontSize: '13px', fontWeight: 600, cursor: 'pointer' }}>{val}</button>
  )

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, overflowY: 'auto', padding: '20px' }}>
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '32px', width: '600px', maxWidth: '95vw' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#e8eaf0', marginBottom: '24px' }}>Nowe ryzyko — ISO 27001:2022</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <F label="Tytuł ryzyka">
              <input required minLength={3} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Krótki opis ryzyka" style={iStyle} />
            </F>
            <F label="Opis">
              <textarea required rows={2} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} placeholder="Szczegółowy opis..." style={{ ...iStyle, resize: 'vertical' }} />
            </F>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <F label="Zagrożenie (Threat)">
                <input value={form.threat} onChange={e => setForm({ ...form, threat: e.target.value })} placeholder="Co może spowodować ryzyko?" style={iStyle} />
              </F>
              <F label="Podatność (Vulnerability)">
                <input value={form.vulnerability} onChange={e => setForm({ ...form, vulnerability: e.target.value })} placeholder="Jaka słabość jest wykorzystywana?" style={iStyle} />
              </F>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <F label="Kategoria">
                <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} style={iStyle}>
                  <option value="CONFIDENTIALITY">Poufność</option>
                  <option value="INTEGRITY">Integralność</option>
                  <option value="AVAILABILITY">Dostępność</option>
                  <option value="PHYSICAL">Fizyczne</option>
                  <option value="LEGAL">Prawne</option>
                  <option value="OTHER">Inne</option>
                </select>
              </F>
              <F label="Podejście do ryzyka">
                <select value={form.treatment} onChange={e => setForm({ ...form, treatment: e.target.value })} style={iStyle}>
                  <option value="MITIGATE">Mitigacja</option>
                  <option value="ACCEPT">Akceptacja</option>
                  <option value="TRANSFER">Transfer</option>
                  <option value="AVOID">Unikanie</option>
                </select>
              </F>
            </div>
            {/* Score calculator */}
            <div style={{ background: '#0f1117', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '14px 16px' }}>
              <div style={{ fontSize: '12px', color: '#8b90a0', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '10px' }}>OCENA RYZYKA (1=Bardzo niskie, 5=Bardzo wysokie)</div>
              <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Prawdopodobieństwo</div>
                  <div style={{ display: 'flex', gap: '4px' }}>{[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={prob} set={setProb} />)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Wpływ</div>
                  <div style={{ display: 'flex', gap: '4px' }}>{[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={impact} set={setImpact} />)}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wynik</div>
                  <div style={{ fontSize: '28px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: lvl.color }}>{score}</div>
                  <div style={{ fontSize: '11px', color: lvl.color }}>{lvl.label}</div>
                </div>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <F label="Właściciel ryzyka">
                <input required value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} placeholder="Imię i nazwisko" style={iStyle} />
              </F>
            </div>
            <F label="Plan mitigacji">
              <textarea rows={2} value={form.mitigationPlan} onChange={e => setForm({ ...form, mitigationPlan: e.target.value })} placeholder="Planowane działania zaradcze..." style={{ ...iStyle, resize: 'vertical' }} />
            </F>
          </div>
          {error && <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>{error}</div>}
          <div style={{ display: 'flex', gap: '8px', marginTop: '20px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>Anuluj</button>
            <button type="submit" disabled={loading} style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: loading ? 0.7 : 1 }}>
              {loading ? 'Tworzenie...' : 'Utwórz ryzyko'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
