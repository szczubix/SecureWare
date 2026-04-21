'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { SEVERITY_LABELS, ASSET_TYPE_LABELS } from '@/lib/utils'

interface SearchResult {
  id: string
  href: string
  number: string
  title: string
  meta: string
  badge: string
  badgeColor: string
  badgeBg: string
  type: 'incident' | 'asset' | 'risk'
}

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: '#fca5a5', HIGH: '#fdba74', MEDIUM: '#fcd34d', LOW: '#93c5fd',
}

const RISK_SCORE_COLOR = (s: number) => s >= 15 ? '#fca5a5' : s >= 10 ? '#fdba74' : s >= 5 ? '#fcd34d' : '#86efac'
const RISK_SCORE_LABEL = (s: number) => s >= 15 ? 'Krytyczne' : s >= 10 ? 'Wysokie' : s >= 5 ? 'Średnie' : 'Niskie'

const STATUS_PL: Record<string, string> = {
  NEW: 'Nowy', IN_PROGRESS: 'W toku', ANALYSIS: 'Analiza', CLOSED: 'Zamknięty',
  OPEN: 'Otwarte', IN_TREATMENT: 'W trakcie', ACCEPTED: 'Zaakceptowane',
}

const CLASS_PL: Record<string, string> = {
  PUBLIC: 'Publiczne', INTERNAL: 'Wewnętrzne', CONFIDENTIAL: 'Poufne', RESTRICTED: 'Zastrzeżone',
}

export function GlobalSearch() {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [active, setActive] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const debRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Ctrl+K / Cmd+K
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setOpen(o => !o)
      }
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50)
      setQuery('')
      setResults([])
      setActive(0)
    }
  }, [open])

  const search = useCallback(async (q: string) => {
    if (q.length < 2) { setResults([]); return }
    setLoading(true)
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
    if (!res.ok) { setLoading(false); return }
    const data = await res.json()

    const all: SearchResult[] = [
      ...data.incidents.map((i: { id: string; incidentNumber: string; title: string; severity: string; status: string }) => ({
        id: i.id, href: `/incidents/${i.id}`,
        number: i.incidentNumber, title: i.title,
        meta: STATUS_PL[i.status] || i.status,
        badge: SEVERITY_LABELS[i.severity] || i.severity,
        badgeColor: SEVERITY_COLOR[i.severity] || '#8b90a0',
        badgeBg: 'rgba(255,255,255,0.05)',
        type: 'incident' as const,
      })),
      ...data.assets.map((a: { id: string; assetNumber: string; name: string; type: string; classification: string }) => ({
        id: a.id, href: `/assets/${a.id}`,
        number: a.assetNumber, title: a.name,
        meta: CLASS_PL[a.classification] || a.classification,
        badge: ASSET_TYPE_LABELS[a.type] || a.type,
        badgeColor: '#93c5fd',
        badgeBg: 'rgba(59,130,246,0.1)',
        type: 'asset' as const,
      })),
      ...data.risks.map((r: { id: string; riskNumber: string; title: string; riskScore: number; status: string }) => ({
        id: r.id, href: `/risks/${r.id}`,
        number: r.riskNumber, title: r.title,
        meta: STATUS_PL[r.status] || r.status,
        badge: `${r.riskScore} · ${RISK_SCORE_LABEL(r.riskScore)}`,
        badgeColor: RISK_SCORE_COLOR(r.riskScore),
        badgeBg: 'rgba(255,255,255,0.05)',
        type: 'risk' as const,
      })),
    ]

    setResults(all)
    setActive(0)
    setLoading(false)
  }, [])

  useEffect(() => {
    if (debRef.current) clearTimeout(debRef.current)
    debRef.current = setTimeout(() => search(query), 250)
    return () => { if (debRef.current) clearTimeout(debRef.current) }
  }, [query, search])

  function navigate(href: string) {
    router.push(href)
    setOpen(false)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive(a => Math.min(a + 1, results.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive(a => Math.max(a - 1, 0))
    } else if (e.key === 'Enter' && results[active]) {
      navigate(results[active].href)
    }
  }

  const TYPE_LABELS = { incident: 'Incydenty', asset: 'Aktywa', risk: 'Ryzyka' }
  const types = ['incident', 'asset', 'risk'] as const

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 40,
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '9px 14px',
          background: '#161922', border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '8px', color: '#555b6e', fontSize: '12px',
          cursor: 'pointer', boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
          transition: 'border-color 0.15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(59,130,246,0.4)')}
        onMouseLeave={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)')}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
        </svg>
        Szukaj
        <kbd style={{ padding: '1px 5px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '3px', fontSize: '10px', fontFamily: 'IBM Plex Mono, monospace', color: '#3a3f52' }}>Ctrl K</kbd>
      </button>
    )
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, zIndex: 50, display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '80px' }}
      onClick={e => { if (e.target === e.currentTarget) setOpen(false) }}
    >
      {/* Backdrop */}
      <div style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }} />

      {/* Modal */}
      <div style={{ position: 'relative', width: '600px', maxWidth: '95vw', background: '#161922', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 24px 64px rgba(0,0,0,0.6)', overflow: 'hidden' }}>

        {/* Search input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '14px 16px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#555b6e" strokeWidth="2" style={{ flexShrink: 0 }}>
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <input
            ref={inputRef}
            type="text"
            placeholder="Szukaj w incydentach, aktywach, ryzykach..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: '#e8eaf0', fontSize: '14px', fontFamily: 'inherit' }}
          />
          {loading && (
            <div style={{ width: '14px', height: '14px', border: '2px solid rgba(59,130,246,0.3)', borderTopColor: '#3b82f6', borderRadius: '50%', animation: 'spin 0.6s linear infinite', flexShrink: 0 }} />
          )}
          <kbd onClick={() => setOpen(false)} style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '11px', color: '#555b6e', cursor: 'pointer', fontFamily: 'IBM Plex Mono, monospace' }}>Esc</kbd>
        </div>

        {/* Results */}
        <div style={{ maxHeight: '420px', overflowY: 'auto' }}>
          {query.length < 2 && (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: '#3a3f52', fontSize: '13px' }}>
              Wpisz co najmniej 2 znaki aby wyszukać
            </div>
          )}
          {query.length >= 2 && !loading && results.length === 0 && (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: '#3a3f52', fontSize: '13px' }}>
              Brak wyników dla &ldquo;{query}&rdquo;
            </div>
          )}
          {results.length > 0 && (() => {
            let globalIdx = 0
            return types.map(type => {
              const group = results.filter(r => r.type === type)
              if (group.length === 0) return null
              return (
                <div key={type}>
                  <div style={{ padding: '8px 16px 4px', fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    {TYPE_LABELS[type]}
                  </div>
                  {group.map(item => {
                    const idx = globalIdx++
                    const isActive = idx === active
                    return (
                      <div
                        key={item.id}
                        onClick={() => navigate(item.href)}
                        onMouseEnter={() => setActive(idx)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: '10px',
                          padding: '10px 16px', cursor: 'pointer',
                          background: isActive ? 'rgba(59,130,246,0.08)' : 'transparent',
                          borderLeft: isActive ? '2px solid #3b82f6' : '2px solid transparent',
                          transition: 'background 0.1s',
                        }}
                      >
                        <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#3b82f6', flexShrink: 0, minWidth: '72px' }}>{item.number}</span>
                        <span style={{ flex: 1, fontSize: '13px', color: '#c8ccd6', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.title}</span>
                        <span style={{ fontSize: '11px', color: '#555b6e', flexShrink: 0 }}>{item.meta}</span>
                        <span style={{ flexShrink: 0, padding: '2px 7px', borderRadius: '3px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', color: item.badgeColor, background: item.badgeBg, whiteSpace: 'nowrap' }}>{item.badge}</span>
                      </div>
                    )
                  })}
                </div>
              )
            })
          })()}
        </div>

        {/* Footer */}
        {results.length > 0 && (
          <div style={{ padding: '8px 16px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '14px', fontSize: '11px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace' }}>
            <span>↑↓ nawigacja</span>
            <span>↵ otwórz</span>
            <span>Esc zamknij</span>
          </div>
        )}
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
