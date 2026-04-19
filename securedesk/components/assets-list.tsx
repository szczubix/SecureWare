'use client'

import { useState, useEffect, useCallback } from 'react'
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

const classColors: Record<string, { bg: string; text: string; border: string }> = {
  RESTRICTED: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  CONFIDENTIAL: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  INTERNAL: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  PUBLIC: { bg: 'rgba(34,197,94,0.15)', text: '#86efac', border: 'rgba(34,197,94,0.25)' },
}

interface StatsData {
  total: number
  restricted: number
  noOwner: number
  overdueReview: number
}

export function AssetsList() {
  const [assets, setAssets] = useState<Asset[]>([])
  const [stats, setStats] = useState<StatsData>({ total: 0, restricted: 0, noOwner: 0, overdueReview: 0 })
  const [search, setSearch] = useState('')
  const [filterType, setFilterType] = useState('')
  const [filterClass, setFilterClass] = useState('')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const fetchAssets = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (filterType) params.set('type', filterType)
    if (filterClass) params.set('classification', filterClass)

    const res = await fetch(`/api/assets?${params}`)
    const data = await res.json()
    setAssets(data.data || [])
    setLoading(false)
  }, [search, filterType, filterClass])

  useEffect(() => {
    fetchAssets()
  }, [fetchAssets])

  useEffect(() => {
    async function loadStats() {
      const [allRes, noOwnerRes, overdueRes] = await Promise.all([
        fetch('/api/assets'),
        fetch('/api/assets?noOwner=true'),
        fetch('/api/assets?overdueReview=true'),
      ])
      const [all, noOwner, overdue] = await Promise.all([
        allRes.json(), noOwnerRes.json(), overdueRes.json(),
      ])
      const allAssets: Asset[] = all.data || []
      setStats({
        total: allAssets.length,
        restricted: allAssets.filter((a) => a.classification === 'RESTRICTED').length,
        noOwner: (noOwner.data || []).length,
        overdueReview: (overdue.data || []).length,
      })
    }
    loadStats()
  }, [assets])

  const isOverdue = (date: string | null) => date && new Date(date) < new Date()

  return (
    <div style={{ padding: '24px', flex: 1 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Aktywa</h1>
          <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>
            Rejestr aktywów informacyjnych organizacji
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer' }}
        >
          + Nowe aktywo
        </button>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
        {[
          { label: 'Aktywów łącznie', value: stats.total, color: '#e8eaf0', bg: 'rgba(255,255,255,0.05)' },
          { label: 'Restricted', value: stats.restricted, color: '#fca5a5', bg: 'rgba(239,68,68,0.1)' },
          { label: 'Bez właściciela', value: stats.noOwner, color: '#fcd34d', bg: 'rgba(245,158,11,0.1)' },
          { label: 'Przegląd przeterminowany', value: stats.overdueReview, color: '#fcd34d', bg: 'rgba(245,158,11,0.1)' },
        ].map((stat) => (
          <div key={stat.label} style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
            <div style={{ fontSize: '28px', fontWeight: 600, color: stat.color, fontFamily: 'IBM Plex Mono, monospace' }}>
              {stat.value}
            </div>
            <div style={{ fontSize: '12px', color: '#8b90a0', marginTop: '4px' }}>{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Szukaj aktywów..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, minWidth: '200px', padding: '7px 12px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none' }}
        />
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{ padding: '7px 10px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px' }}
        >
          <option value="">Wszystkie typy</option>
          <option value="HARDWARE">Sprzęt</option>
          <option value="SOFTWARE">Oprogramowanie</option>
          <option value="DATA">Dane</option>
          <option value="CLOUD_SERVICE">Usługa cloud</option>
          <option value="INFRASTRUCTURE">Infrastruktura</option>
          <option value="OTHER">Inne</option>
        </select>
        <select
          value={filterClass}
          onChange={(e) => setFilterClass(e.target.value)}
          style={{ padding: '7px 10px', background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px' }}
        >
          <option value="">Wszystkie klasy</option>
          <option value="RESTRICTED">Zastrzeżony</option>
          <option value="CONFIDENTIAL">Poufny</option>
          <option value="INTERNAL">Wewnętrzny</option>
          <option value="PUBLIC">Publiczny</option>
        </select>
      </div>

      {/* Table */}
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              {['ID', 'Aktywo', 'Typ', 'Klasyfikacja', 'Właściciel', 'Incydenty', 'Przegląd'].map((col) => (
                <th key={col} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Ładowanie...</td></tr>
            ) : assets.length === 0 ? (
              <tr><td colSpan={7} style={{ padding: '32px', textAlign: 'center', color: '#555b6e', fontSize: '13px' }}>Brak aktywów spełniających kryteria</td></tr>
            ) : assets.map((asset) => {
              const cc = classColors[asset.classification] || classColors.INTERNAL
              const overdue = isOverdue(asset.nextReviewAt)
              return (
                <tr
                  key={asset.id}
                  style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.02)')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '12px 16px' }}>
                    <Link href={`/assets/${asset.id}`} style={{ textDecoration: 'none' }}>
                      <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>
                        {asset.assetNumber}
                      </span>
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
                      {asset.businessOwner || asset.technicalOwner || (
                        <span style={{ color: '#f59e0b', fontSize: '11px' }}>Brak właściciela</span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {asset._count.incidents > 0 ? (
                      <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: 'rgba(239,68,68,0.1)', color: '#fca5a5', border: '1px solid rgba(239,68,68,0.2)' }}>
                        {asset._count.incidents}
                      </span>
                    ) : (
                      <span style={{ color: '#3a3f52', fontSize: '12px' }}>—</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    {asset.nextReviewAt ? (
                      <span style={{ fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', color: overdue ? '#fca5a5' : '#555b6e' }}>
                        {overdue ? '⚠ ' : ''}{formatDateShort(asset.nextReviewAt)}
                      </span>
                    ) : (
                      <span style={{ color: '#3a3f52', fontSize: '12px' }}>—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

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
  const [form, setForm] = useState({
    name: '',
    type: 'HARDWARE',
    classification: 'INTERNAL',
    description: '',
    location: '',
    businessOwner: '',
    technicalOwner: '',
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')
    const res = await fetch('/api/assets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (res.ok) {
      onCreated()
    } else {
      const data = await res.json()
      setError(data.error?.formErrors?.[0] || 'Błąd podczas tworzenia aktywa')
      setLoading(false)
    }
  }

  const F = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', marginBottom: '5px', fontFamily: 'IBM Plex Mono, monospace' }}>{label}</label>
      {children}
    </div>
  )

  const iStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50 }}>
      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '32px', width: '520px', maxWidth: '95vw' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#e8eaf0', marginBottom: '24px' }}>Nowe aktywo</h2>
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <F label="Nazwa aktywa">
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nazwa zasobu informacyjnego" style={iStyle} />
            </F>
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
            <F label="Lokalizacja">
              <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="Np. serwerownia, chmura AWS" style={iStyle} />
            </F>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <F label="Właściciel biznesowy">
                <input value={form.businessOwner} onChange={(e) => setForm({ ...form, businessOwner: e.target.value })} placeholder="Imię i nazwisko" style={iStyle} />
              </F>
              <F label="Właściciel techniczny">
                <input value={form.technicalOwner} onChange={(e) => setForm({ ...form, technicalOwner: e.target.value })} placeholder="Imię i nazwisko" style={iStyle} />
              </F>
            </div>
            <F label="Opis">
              <textarea rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Opis aktywa..." style={{ ...iStyle, resize: 'vertical' }} />
            </F>
          </div>
          {error && (
            <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>
              {error}
            </div>
          )}
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
