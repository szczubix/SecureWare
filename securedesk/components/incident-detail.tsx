'use client'

import { useState } from 'react'
import Link from 'next/link'
import { NIS2Timer } from './nis2-timer'
import { formatDate, SEVERITY_LABELS, STATUS_LABELS, CATEGORY_LABELS, ASSET_TYPE_LABELS, CLASSIFICATION_LABELS } from '@/lib/utils'

interface Action {
  id: string
  content: string
  authorName: string
  createdAt: string
}

interface Evidence {
  id: string
  filename: string
  size: number
  mimeType: string
  createdAt: string
}

interface Asset {
  id: string
  assetNumber: string
  name: string
  type: string
  classification: string
}

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
  nis2StartedAt: string | null
  nis2EarlyWarningSentAt: string | null
  nis2ReportSentAt: string | null
  closedAt: string | null
  closureRootCause: string | null
  closureActions: string | null
  closurePreventive: string | null
  createdAt: string
  actions: Action[]
  evidences: Evidence[]
  assets: { asset: Asset }[]
}

interface Props {
  incident: Incident
  currentUser: { id: string; name: string }
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

export function IncidentDetail({ incident: initial, currentUser }: Props) {
  const [incident, setIncident] = useState(initial)
  const [actions, setActions] = useState(initial.actions)
  const [newAction, setNewAction] = useState('')
  const [savingAction, setSavingAction] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [showClosure, setShowClosure] = useState(initial.status === 'CLOSED')
  const [closure, setClosure] = useState({
    rootCause: initial.closureRootCause || '',
    actions: initial.closureActions || '',
    preventive: initial.closurePreventive || '',
  })

  async function addAction() {
    if (!newAction.trim()) return
    setSavingAction(true)
    const res = await fetch(`/api/incidents/${incident.id}/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: newAction }),
    })
    if (res.ok) {
      const data = await res.json()
      setActions((prev) => [...prev, data.data])
      setNewAction('')
    }
    setSavingAction(false)
  }

  async function updateStatus(status: string) {
    setUpdatingStatus(true)
    const body: Record<string, unknown> = { status }
    if (status === 'CLOSED') {
      body.closureRootCause = closure.rootCause
      body.closureActions = closure.actions
      body.closurePreventive = closure.preventive
    }
    const res = await fetch(`/api/incidents/${incident.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (res.ok) {
      const data = await res.json()
      setIncident((prev) => ({ ...prev, ...data.data }))
      const reloaded = await fetch(`/api/incidents/${incident.id}`)
      const reloadedData = await reloaded.json()
      if (reloadedData.data) setActions(reloadedData.data.actions)
    }
    setUpdatingStatus(false)
  }

  const sevColor = SEVERITY_COLORS[incident.severity] || SEVERITY_COLORS.LOW
  const stColor = STATUS_COLORS[incident.status] || STATUS_COLORS.NEW

  return (
    <div style={{ padding: '24px', display: 'flex', gap: '24px' }}>
      {/* Left column */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Breadcrumb */}
        <div style={{ fontSize: '12px', color: '#555b6e', marginBottom: '16px', fontFamily: 'IBM Plex Mono, monospace' }}>
          <Link href="/incidents" style={{ color: '#3b82f6', textDecoration: 'none' }}>Incydenty</Link>
          {' › '}
          {incident.incidentNumber}
        </div>

        {/* Title */}
        <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#e8eaf0', margin: '0 0 12px' }}>
          {incident.title}
        </h1>

        {/* Badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <Badge bg={sevColor.bg} text={sevColor.text} border={sevColor.border}>
            {SEVERITY_LABELS[incident.severity]}
          </Badge>
          <Badge bg={stColor.bg} text={stColor.text} border={stColor.border}>
            {STATUS_LABELS[incident.status]}
          </Badge>
          {incident.nis2Active && (
            <Badge bg="rgba(245,158,11,0.15)" text="#fcd34d" border="rgba(245,158,11,0.25)">
              NIS2 Art. 21
            </Badge>
          )}
          <Badge bg="rgba(59,130,246,0.1)" text="#93c5fd" border="rgba(59,130,246,0.2)">
            A.6.8 · A.8.15
          </Badge>
        </div>

        {/* NIS2 Timer */}
        {incident.nis2Active && incident.nis2StartedAt && (
          <NIS2Timer
            startedAt={incident.nis2StartedAt}
            earlyWarningSentAt={incident.nis2EarlyWarningSentAt}
            reportSentAt={incident.nis2ReportSentAt}
          />
        )}

        {/* Description */}
        <Section title="Opis zdarzenia">
          <p style={{ fontSize: '14px', color: '#8b90a0', lineHeight: 1.7, margin: 0 }}>
            {incident.description}
          </p>
        </Section>

        {/* Timeline */}
        <Section title="Oś czasu działań">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {actions.map((action) => (
              <div key={action.id} style={{
                padding: '12px 14px',
                background: '#0f1117',
                borderRadius: '6px',
                borderLeft: '2px solid rgba(59,130,246,0.3)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontSize: '12px', color: '#3b82f6', fontWeight: 500 }}>{action.authorName}</span>
                  <span style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {formatDate(action.createdAt)}
                  </span>
                </div>
                <p style={{ fontSize: '13px', color: '#8b90a0', margin: 0, lineHeight: 1.6 }}>
                  {action.content}
                </p>
              </div>
            ))}
          </div>

          {/* Add action */}
          {incident.status !== 'CLOSED' && (
            <div style={{ marginTop: '16px' }}>
              <textarea
                rows={3}
                value={newAction}
                onChange={(e) => setNewAction(e.target.value)}
                placeholder="Dodaj działanie, notatkę lub aktualizację statusu..."
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  background: '#0f1117',
                  border: '1px solid rgba(255,255,255,0.1)',
                  borderRadius: '6px',
                  color: '#e8eaf0',
                  fontSize: '13px',
                  outline: 'none',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button
                  onClick={addAction}
                  disabled={savingAction || !newAction.trim()}
                  style={{
                    padding: '7px 16px',
                    background: '#3b82f6',
                    color: '#fff',
                    border: 'none',
                    borderRadius: '6px',
                    fontSize: '13px',
                    cursor: 'pointer',
                    opacity: savingAction || !newAction.trim() ? 0.5 : 1,
                  }}
                >
                  {savingAction ? 'Zapisywanie...' : 'Dodaj działanie'}
                </button>
              </div>
            </div>
          )}
        </Section>

        {/* Closure */}
        {(showClosure || incident.status === 'CLOSED') && (
          <Section title="Zamknięcie incydentu">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <ClosureField label="Przyczyna źródłowa" value={closure.rootCause} onChange={(v) => setClosure({ ...closure, rootCause: v })} disabled={incident.status === 'CLOSED'} />
              <ClosureField label="Podjęte działania" value={closure.actions} onChange={(v) => setClosure({ ...closure, actions: v })} disabled={incident.status === 'CLOSED'} />
              <ClosureField label="Działania zapobiegawcze" value={closure.preventive} onChange={(v) => setClosure({ ...closure, preventive: v })} disabled={incident.status === 'CLOSED'} />
              {incident.status !== 'CLOSED' && (
                <button
                  onClick={() => updateStatus('CLOSED')}
                  disabled={updatingStatus}
                  style={{ padding: '8px 16px', background: 'rgba(34,197,94,0.15)', color: '#86efac', border: '1px solid rgba(34,197,94,0.25)', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', alignSelf: 'flex-start' }}
                >
                  Zamknij incydent
                </button>
              )}
            </div>
          </Section>
        )}
      </div>

      {/* Right sidebar */}
      <div style={{ width: '280px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Details card */}
        <SideCard title="Szczegóły">
          <DetailRow label="Status">
            <select
              value={incident.status}
              disabled={incident.status === 'CLOSED' || updatingStatus}
              onChange={(e) => updateStatus(e.target.value)}
              style={{ background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: '#e8eaf0', fontSize: '12px', padding: '4px 8px', cursor: 'pointer' }}
            >
              <option value="NEW">Nowy</option>
              <option value="IN_PROGRESS">W toku</option>
              <option value="ANALYSIS">Analiza</option>
              <option value="CLOSED">Zamknięty</option>
            </select>
          </DetailRow>
          <DetailRow label="Klasyfikacja">{SEVERITY_LABELS[incident.severity]}</DetailRow>
          <DetailRow label="Kategoria">{CATEGORY_LABELS[incident.category]}</DetailRow>
          <DetailRow label="Zgłaszający">{incident.reportedBy}</DetailRow>
          <DetailRow label="Otwarto">{formatDate(incident.createdAt)}</DetailRow>
          {incident.closedAt && <DetailRow label="Zamknięto">{formatDate(incident.closedAt)}</DetailRow>}
        </SideCard>

        {/* Assets */}
        {incident.assets.length > 0 && (
          <SideCard title="Powiązane aktywa">
            {incident.assets.map(({ asset }) => (
              <div key={asset.id} style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '12px', color: '#e8eaf0', fontWeight: 500 }}>{asset.name}</div>
                <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
                  {asset.assetNumber} · {ASSET_TYPE_LABELS[asset.type]}
                </div>
              </div>
            ))}
          </SideCard>
        )}

        {/* Evidence */}
        <SideCard title={`Dowody (${incident.evidences.length})`}>
          {incident.evidences.length === 0 ? (
            <p style={{ fontSize: '12px', color: '#555b6e' }}>Brak załączonych dowodów</p>
          ) : incident.evidences.map((ev) => (
            <div key={ev.id} style={{ marginBottom: '8px' }}>
              <div style={{ fontSize: '12px', color: '#93c5fd' }}>{ev.filename}</div>
              <div style={{ fontSize: '11px', color: '#555b6e' }}>
                {(ev.size / 1024).toFixed(1)} KB · {formatDate(ev.createdAt)}
              </div>
            </div>
          ))}
        </SideCard>

        {/* Actions */}
        <SideCard title="Akcje">
          {incident.status !== 'CLOSED' && (
            <button
              onClick={() => setShowClosure(!showClosure)}
              style={{ display: 'block', width: '100%', marginBottom: '8px', padding: '7px', background: 'rgba(34,197,94,0.1)', color: '#86efac', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
            >
              Zamknij incydent
            </button>
          )}
          <Link href="/incidents" style={{ display: 'block', padding: '7px', background: 'rgba(255,255,255,0.04)', color: '#8b90a0', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', fontSize: '12px', textDecoration: 'none', textAlign: 'center' }}>
            ← Powrót do listy
          </Link>
        </SideCard>
      </div>
    </div>
  )
}

function Badge({ bg, text, border, children }: { bg: string; text: string; border: string; children: React.ReactNode }) {
  return (
    <span style={{ padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: bg, color: text, border: `1px solid ${border}` }}>
      {children}
    </span>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', color: '#555b6e', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '12px', marginTop: 0 }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function SideCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
      <h4 style={{ fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', color: '#555b6e', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 12px' }}>
        {title}
      </h4>
      {children}
    </div>
  )
}

function DetailRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
      <span style={{ fontSize: '12px', color: '#555b6e' }}>{label}</span>
      <span style={{ fontSize: '12px', color: '#8b90a0' }}>{children}</span>
    </div>
  )
}

function ClosureField({ label, value, onChange, disabled }: { label: string; value: string; onChange: (v: string) => void; disabled: boolean }) {
  return (
    <div>
      <label style={{ display: 'block', fontSize: '11px', color: '#555b6e', marginBottom: '4px', fontFamily: 'IBM Plex Mono, monospace' }}>
        {label}
      </label>
      <textarea
        rows={2}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        style={{ width: '100%', padding: '8px 10px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '4px', color: disabled ? '#555b6e' : '#e8eaf0', fontSize: '12px', outline: 'none', resize: 'vertical', boxSizing: 'border-box' }}
      />
    </div>
  )
}
