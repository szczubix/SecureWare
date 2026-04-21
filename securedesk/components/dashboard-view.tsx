'use client'

import { useEffect, useState, useCallback } from 'react'
import Link from 'next/link'
import { SEVERITY_LABELS, STATUS_LABELS, ASSET_TYPE_LABELS, formatDateShort } from '@/lib/utils'

type Nis2Incident = {
  id: string
  incidentNumber: string
  title: string
  severity: string
  status: string
  nis2StartedAt: string | null
  nis2EarlyWarningSentAt: string | null
  nis2ReportSentAt: string | null
}

type AssetOverdue = {
  id: string
  assetNumber: string
  name: string
  type: string
  nextReviewAt: string
}

type RecentIncident = {
  id: string
  incidentNumber: string
  title: string
  severity: string
  status: string
  createdAt: string
}

type ChartPoint = { date: string; count: number }

type TopRisk = {
  id: string
  riskNumber: string
  title: string
  riskScore: number
  category: string
  owner: string
  treatment: string
  status: string
}

type RiskMatrixPoint = { probability: number; impact: number }

type DashboardData = {
  openCount: number
  severityMap: Record<string, number>
  nis2Active: Nis2Incident[]
  assetsOverdue: AssetOverdue[]
  recentIncidents: RecentIncident[]
  chartData: ChartPoint[]
  riskOpenCount: number
  riskCriticalCount: number
  riskOverdueCount: number
  topRisks: TopRisk[]
  riskMatrixData: RiskMatrixPoint[]
}

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'text-red-400',
  HIGH: 'text-orange-400',
  MEDIUM: 'text-yellow-400',
  LOW: 'text-blue-400',
  INFO: 'text-gray-400',
}

const SEVERITY_BG: Record<string, string> = {
  CRITICAL: 'bg-red-500/20 border-red-500/40',
  HIGH: 'bg-orange-500/20 border-orange-500/40',
  MEDIUM: 'bg-yellow-500/20 border-yellow-500/40',
  LOW: 'bg-blue-500/20 border-blue-500/40',
  INFO: 'bg-gray-500/20 border-gray-500/40',
}

function useNis2Elapsed(startedAt: string | null) {
  const [elapsed, setElapsed] = useState(0)
  useEffect(() => {
    if (!startedAt) return
    const start = new Date(startedAt).getTime()
    const tick = () => setElapsed(Date.now() - start)
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [startedAt])
  return elapsed
}

function NIS2Row({ inc }: { inc: Nis2Incident }) {
  const elapsed = useNis2Elapsed(inc.nis2StartedAt)
  const hours = elapsed / (1000 * 60 * 60)

  const step1Done = !!inc.nis2EarlyWarningSentAt
  const step2Done = !!inc.nis2ReportSentAt
  const step3Done = false

  const deadline = !step1Done ? 24 : !step2Done ? 72 : !step3Done ? 24 * 30 : null
  const remaining = deadline !== null ? deadline - hours : null
  const overdue = remaining !== null && remaining < 0

  function fmt(ms: number) {
    const h = Math.floor(Math.abs(ms) / (1000 * 60 * 60))
    const m = Math.floor((Math.abs(ms) % (1000 * 60 * 60)) / (1000 * 60))
    const s = Math.floor((Math.abs(ms) % (1000 * 60)) / 1000)
    return `${h}h ${m}m ${s}s`
  }

  const remainingMs = remaining !== null ? remaining * 60 * 60 * 1000 : null

  return (
    <Link href={`/incidents/${inc.id}`} className="block hover:bg-white/5 transition-colors rounded-lg px-3 py-2 -mx-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-xs font-mono font-semibold ${SEVERITY_COLORS[inc.severity] || 'text-gray-400'}`}>
              {inc.incidentNumber}
            </span>
            <span className="text-sm text-[var(--foreground)] truncate">{inc.title}</span>
          </div>
          <div className="flex gap-3 mt-1">
            {[
              { label: '24h ostrzeżenie', done: step1Done },
              { label: '72h raport', done: step2Done },
              { label: '30d końcowy', done: step3Done },
            ].map((s, i) => (
              <span key={i} className={`text-xs px-1.5 py-0.5 rounded ${s.done ? 'bg-green-500/20 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                {s.done ? '✓' : '○'} {s.label}
              </span>
            ))}
          </div>
        </div>
        {remainingMs !== null && (
          <div className={`text-right shrink-0 font-mono text-sm font-semibold ${overdue ? 'text-red-400' : 'text-amber-400'}`}>
            {overdue ? '-' : ''}{fmt(remainingMs)}
            <div className="text-xs font-normal text-gray-500">{overdue ? 'OPÓŹNIONE' : 'pozostało'}</div>
          </div>
        )}
        {remainingMs === null && (
          <span className="text-xs text-green-400 shrink-0">Zakończone</span>
        )}
      </div>
    </Link>
  )
}

const RISK_CATEGORY_PL: Record<string, string> = {
  CONFIDENTIALITY: 'Poufność', INTEGRITY: 'Integralność', AVAILABILITY: 'Dostępność',
  PHYSICAL: 'Fizyczne', LEGAL: 'Prawne', OTHER: 'Inne',
}
const RISK_TREATMENT_PL: Record<string, string> = {
  ACCEPT: 'Akceptacja', MITIGATE: 'Mitigacja', TRANSFER: 'Transfer', AVOID: 'Unikanie',
}

function riskScoreLevel(s: number) {
  if (s >= 15) return { label: 'Krytyczne', color: '#fca5a5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)' }
  if (s >= 10) return { label: 'Wysokie',   color: '#fdba74', bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.3)' }
  if (s >= 5)  return { label: 'Średnie',   color: '#fcd34d', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)' }
  return             { label: 'Niskie',    color: '#86efac', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.3)' }
}

function cellColor(p: number, i: number) {
  const s = p * i
  if (s >= 15) return 'rgba(239,68,68,0.4)'
  if (s >= 10) return 'rgba(249,115,22,0.35)'
  if (s >= 5)  return 'rgba(245,158,11,0.3)'
  return 'rgba(34,197,94,0.2)'
}

function MiniRiskMatrix({ points }: { points: RiskMatrixPoint[] }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-semibold text-[var(--foreground)]">Macierz ryzyk</h2>
        <Link href="/risks" className="text-xs text-blue-400 hover:underline">Rejestr →</Link>
      </div>
      <div style={{ display: 'flex', gap: '6px', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '120px', paddingBottom: '16px' }}>
          {[5,4,3,2,1].map(p => (
            <div key={p} style={{ fontSize: '9px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'right', lineHeight: '22px' }}>{p}</div>
          ))}
        </div>
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,22px)', gridTemplateRows: 'repeat(5,22px)', gap: '2px' }}>
            {[5,4,3,2,1].map(p =>
              [1,2,3,4,5].map(i => {
                const count = points.filter(r => r.probability === p && r.impact === i).length
                return (
                  <div key={`${p}-${i}`}
                    style={{ background: cellColor(p, i), borderRadius: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {count > 0 && <span style={{ fontSize: '8px', fontWeight: 700, color: '#fff', fontFamily: 'IBM Plex Mono, monospace' }}>{count}</span>}
                  </div>
                )
              })
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,22px)', gap: '2px', marginTop: '3px' }}>
            {[1,2,3,4,5].map(i => (
              <div key={i} style={{ fontSize: '9px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textAlign: 'center' }}>{i}</div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', paddingBottom: '18px', marginLeft: '4px' }}>
          {[
            { c: 'rgba(239,68,68,0.5)',   l: '≥15' },
            { c: 'rgba(249,115,22,0.45)', l: '10-14' },
            { c: 'rgba(245,158,11,0.4)',  l: '5-9' },
            { c: 'rgba(34,197,94,0.35)',  l: '1-4' },
          ].map(({ c, l }) => (
            <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '1px', background: c, flexShrink: 0 }} />
              <span style={{ fontSize: '9px', color: '#555b6e' }}>{l}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function BarChart({ data }: { data: ChartPoint[] }) {
  const max = Math.max(...data.map(d => d.count), 1)
  const last7 = data.slice(-7)

  return (
    <div className="mt-2">
      <div className="flex items-end gap-1 h-20">
        {data.map((d, i) => {
          const pct = (d.count / max) * 100
          const isLast7 = i >= data.length - 7
          return (
            <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full group relative">
              <div
                className={`w-full rounded-sm transition-all ${isLast7 ? 'bg-blue-500/80' : 'bg-blue-500/30'} min-h-[2px]`}
                style={{ height: `${Math.max(pct, 2)}%` }}
              />
              {d.count > 0 && (
                <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-[var(--card)] border border-[var(--border)] text-xs px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {d.date.slice(5)}: {d.count}
                </div>
              )}
            </div>
          )
        })}
      </div>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>{data[0]?.date.slice(5)}</span>
        <span className="text-gray-400">ostatnie 30 dni</span>
        <span>{data[data.length - 1]?.date.slice(5)}</span>
      </div>
      <div className="text-xs text-gray-500 mt-1">
        Ostatnie 7 dni: {last7.reduce((a, b) => a + b.count, 0)} incydentów
      </div>
    </div>
  )
}

export function DashboardView() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/dashboard')
      if (res.ok) {
        const json = await res.json()
        setData(json.data)
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, 60_000)
    return () => clearInterval(id)
  }, [load])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Ładowanie...
      </div>
    )
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64 text-red-400">
        Błąd ładowania danych
      </div>
    )
  }

  const criticalCount = data.severityMap['CRITICAL'] || 0
  const highCount = data.severityMap['HIGH'] || 0
  const totalLast30 = data.chartData.reduce((a, b) => a + b.count, 0)
  const hasAnyRisks = data.riskOpenCount > 0 || data.riskCriticalCount > 0

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--foreground)]">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Przegląd operacyjny — {new Date().toLocaleDateString('pl-PL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
      </div>

      {/* Incident stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Otwarte incydenty"
          value={data.openCount}
          sub={data.openCount === 0 ? 'Brak aktywnych' : 'wymagają uwagi'}
          accent={data.openCount > 0 ? 'text-orange-400' : 'text-green-400'}
          href="/incidents"
        />
        <StatCard
          label="Krytyczne / Wysokie"
          value={`${criticalCount} / ${highCount}`}
          sub={criticalCount > 0 ? 'Natychmiastowa reakcja' : 'Bez zagrożeń krytycznych'}
          accent={criticalCount > 0 ? 'text-red-400' : 'text-green-400'}
          href="/incidents?severity=CRITICAL"
        />
        <StatCard
          label="Aktywne NIS2"
          value={data.nis2Active.length}
          sub={data.nis2Active.length > 0 ? 'Trwają odliczania' : 'Brak aktywnych procedur'}
          accent={data.nis2Active.length > 0 ? 'text-amber-400' : 'text-green-400'}
          href="/incidents?nis2=true"
        />
        <StatCard
          label="Aktywa do przeglądu"
          value={data.assetsOverdue.length}
          sub={data.assetsOverdue.length > 0 ? 'Termin minął' : 'Wszystko aktualne'}
          accent={data.assetsOverdue.length > 0 ? 'text-yellow-400' : 'text-green-400'}
          href="/assets"
        />
      </div>

      {/* Risk stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Otwarte ryzyka ISO 27001"
          value={data.riskOpenCount}
          sub={data.riskOpenCount === 0 ? 'Brak aktywnych ryzyk' : 'otwarte lub w trakcie'}
          accent={data.riskOpenCount > 0 ? 'text-amber-400' : 'text-green-400'}
          href="/risks"
        />
        <StatCard
          label="Ryzyka krytyczne (≥15)"
          value={data.riskCriticalCount}
          sub={data.riskCriticalCount > 0 ? 'Wymagają natychmiastowej akcji' : 'Brak ryzyk krytycznych'}
          accent={data.riskCriticalCount > 0 ? 'text-red-400' : 'text-green-400'}
          href="/risks?minScore=15"
        />
        <StatCard
          label="Przeglądy ryzyk po terminie"
          value={data.riskOverdueCount}
          sub={data.riskOverdueCount > 0 ? 'Termin przeglądu minął' : 'Wszystkie przeglądy aktualne'}
          accent={data.riskOverdueCount > 0 ? 'text-yellow-400' : 'text-green-400'}
          href="/risks"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* NIS2 active */}
        <div className="lg:col-span-2 space-y-4">
          <Section title="Aktywne procedury NIS2" count={data.nis2Active.length} href="/incidents?nis2=true" emptyText="Brak aktywnych procedur NIS2">
            {data.nis2Active.map(inc => (
              <NIS2Row key={inc.id} inc={inc} />
            ))}
          </Section>

          {/* Top risks */}
          {hasAnyRisks && (
            <Section title="Top ryzyka (wg wyniku)" count={data.topRisks.length} href="/risks" emptyText="Brak otwartych ryzyk">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-500 text-xs border-b border-[var(--border)]">
                      <th className="text-left py-2 font-normal">Nr</th>
                      <th className="text-left py-2 font-normal">Ryzyko</th>
                      <th className="text-left py-2 font-normal">Wynik</th>
                      <th className="text-left py-2 font-normal">Podejście</th>
                      <th className="text-left py-2 font-normal">Właściciel</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {data.topRisks.map(risk => {
                      const lvl = riskScoreLevel(risk.riskScore)
                      return (
                        <tr key={risk.id} className="hover:bg-white/5 transition-colors">
                          <td className="py-2 pr-3">
                            <Link href={`/risks/${risk.id}`} className="font-mono text-xs text-blue-400 hover:underline whitespace-nowrap">
                              {risk.riskNumber}
                            </Link>
                          </td>
                          <td className="py-2 pr-3">
                            <Link href={`/risks/${risk.id}`} className="hover:text-blue-400 transition-colors line-clamp-1">
                              {risk.title}
                            </Link>
                            <div className="text-xs text-gray-500">{RISK_CATEGORY_PL[risk.category] || risk.category}</div>
                          </td>
                          <td className="py-2 pr-3">
                            <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, background: lvl.bg, color: lvl.color, border: `1px solid ${lvl.border}` }}>
                              {risk.riskScore}
                            </span>
                          </td>
                          <td className="py-2 pr-3 text-xs text-gray-400 whitespace-nowrap">
                            {RISK_TREATMENT_PL[risk.treatment] || risk.treatment}
                          </td>
                          <td className="py-2 text-xs text-gray-500 max-w-[80px] truncate">
                            {risk.owner}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Recent incidents */}
          <Section title="Ostatnie incydenty" count={data.recentIncidents.length} href="/incidents" emptyText="Brak incydentów">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-xs border-b border-[var(--border)]">
                    <th className="text-left py-2 font-normal">Nr</th>
                    <th className="text-left py-2 font-normal">Tytuł</th>
                    <th className="text-left py-2 font-normal">Ważność</th>
                    <th className="text-left py-2 font-normal">Status</th>
                    <th className="text-left py-2 font-normal">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {data.recentIncidents.map(inc => (
                    <tr key={inc.id} className="hover:bg-white/5 transition-colors">
                      <td className="py-2 pr-3">
                        <Link href={`/incidents/${inc.id}`} className="font-mono text-xs text-blue-400 hover:underline">
                          {inc.incidentNumber}
                        </Link>
                      </td>
                      <td className="py-2 pr-3">
                        <Link href={`/incidents/${inc.id}`} className="hover:text-blue-400 transition-colors line-clamp-1">
                          {inc.title}
                        </Link>
                      </td>
                      <td className="py-2 pr-3">
                        <span className={`text-xs font-semibold ${SEVERITY_COLORS[inc.severity] || 'text-gray-400'}`}>
                          {SEVERITY_LABELS[inc.severity] || inc.severity}
                        </span>
                      </td>
                      <td className="py-2 pr-3">
                        <span className="text-xs text-gray-400">
                          {STATUS_LABELS[inc.status] || inc.status}
                        </span>
                      </td>
                      <td className="py-2 text-xs text-gray-500">
                        {formatDateShort(inc.createdAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Trend chart */}
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-sm font-semibold text-[var(--foreground)]">Trend incydentów</h2>
              <span className="text-xs text-gray-500">{totalLast30} / 30 dni</span>
            </div>
            <BarChart data={data.chartData} />
          </div>

          {/* Mini risk matrix */}
          {data.riskMatrixData.length > 0 && (
            <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
              <MiniRiskMatrix points={data.riskMatrixData} />
            </div>
          )}

          {/* Assets overdue */}
          <Section title="Aktywa po terminie przeglądu" count={data.assetsOverdue.length} href="/assets" emptyText="Brak aktywów po terminie">
            <div className="space-y-2">
              {data.assetsOverdue.map(asset => {
                const daysOverdue = Math.floor((Date.now() - new Date(asset.nextReviewAt).getTime()) / (1000 * 60 * 60 * 24))
                return (
                  <Link key={asset.id} href={`/assets/${asset.id}`} className="block hover:bg-white/5 transition-colors rounded-lg px-3 py-2 -mx-3">
                    <div className="flex items-center justify-between">
                      <div className="min-w-0">
                        <div className="text-sm text-[var(--foreground)] truncate">{asset.name}</div>
                        <div className="text-xs text-gray-500">{asset.assetNumber} · {ASSET_TYPE_LABELS[asset.type] || asset.type}</div>
                      </div>
                      <span className="text-xs text-red-400 shrink-0 ml-2">+{daysOverdue}d</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          </Section>

          {/* Severity breakdown */}
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
            <h2 className="text-sm font-semibold text-[var(--foreground)] mb-3">Otwarte wg ważności</h2>
            <div className="space-y-2">
              {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'] as const).map(sev => {
                const count = data.severityMap[sev] || 0
                const total = data.openCount || 1
                const pct = Math.round((count / total) * 100)
                return (
                  <div key={sev}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className={SEVERITY_COLORS[sev]}>{SEVERITY_LABELS[sev]}</span>
                      <span className="text-gray-400">{count}</span>
                    </div>
                    <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          sev === 'CRITICAL' ? 'bg-red-500' :
                          sev === 'HIGH' ? 'bg-orange-500' :
                          sev === 'MEDIUM' ? 'bg-yellow-500' :
                          sev === 'LOW' ? 'bg-blue-500' : 'bg-gray-500'
                        }`}
                        style={{ width: `${count > 0 ? Math.max(pct, 4) : 0}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, accent, href }: { label: string; value: number | string; sub: string; accent: string; href: string }) {
  return (
    <Link href={href} className="block bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 hover:border-blue-500/40 transition-colors">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${accent}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{sub}</div>
    </Link>
  )
}

function Section({ title, count, href, emptyText, children }: { title: string; count: number; href: string; emptyText: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-[var(--foreground)]">{title}</h2>
        <Link href={href} className="text-xs text-blue-400 hover:underline">
          Wszystkie →
        </Link>
      </div>
      {count === 0 ? (
        <p className="text-sm text-gray-500 py-4 text-center">{emptyText}</p>
      ) : (
        <div className="space-y-1">{children}</div>
      )}
    </div>
  )
}
