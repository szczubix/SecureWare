'use client'

import { useState, useRef } from 'react'
import Link from 'next/link'
import { NIS2Timer } from './nis2-timer'
import { formatDate, SEVERITY_LABELS, STATUS_LABELS, CATEGORY_LABELS, ASSET_TYPE_LABELS } from '@/lib/utils'

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
  downloadUrl?: string | null
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
  const [evidences, setEvidences] = useState<Evidence[]>(initial.evidences)
  const [newAction, setNewAction] = useState('')
  const [savingAction, setSavingAction] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [showClosure, setShowClosure] = useState(initial.status === 'CLOSED')
  const [closure, setClosure] = useState({
    rootCause: initial.closureRootCause || '',
    actions: initial.closureActions || '',
    preventive: initial.closurePreventive || '',
  })
  const [nis2Loading, setNis2Loading] = useState<string | null>(null)
  const [uploadingFile, setUploadingFile] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

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
      const rd = await reloaded.json()
      if (rd.data) setActions(rd.data.actions)
    }
    setUpdatingStatus(false)
  }

  async function sendNis2Action(action: 'early_warning' | 'report_72h' | 'final_report') {
    setNis2Loading(action)
    const res = await fetch(`/api/incidents/${incident.id}/nis2`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    })
    if (res.ok) {
      const data = await res.json()
      const now = data.timestamp
      setIncident((prev) => ({
        ...prev,
        ...(action === 'early_warning' ? { nis2EarlyWarningSentAt: now } : {}),
        ...(action === 'report_72h' ? { nis2ReportSentAt: now } : {}),
      }))
      // Reload actions
      const reloaded = await fetch(`/api/incidents/${incident.id}`)
      const rd = await reloaded.json()
      if (rd.data) setActions(rd.data.actions)
    }
    setNis2Loading(null)
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadingFile(true)

    try {
      // 1. Request presigned URL
      const res = await fetch(`/api/incidents/${incident.id}/evidence`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: file.name, size: file.size, mimeType: file.type || 'application/octet-stream' }),
      })

      if (!res.ok) {
        const err = await res.json()
        alert(err.error || 'Błąd przesyłania pliku')
        setUploadingFile(false)
        return
      }

      const { data } = await res.json()

      // 2. Upload directly to MinIO
      await fetch(data.uploadUrl, {
        method: 'PUT',
        body: file,
        headers: { 'Content-Type': file.type || 'application/octet-stream' },
      })

      setEvidences((prev) => [data.evidence, ...prev])
    } catch {
      alert('Błąd połączenia z magazynem plików')
    } finally {
      setUploadingFile(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function deleteEvidence(evidenceId: string) {
    if (!confirm('Usunąć ten dowód?')) return
    const res = await fetch(`/api/incidents/${incident.id}/evidence?evidenceId=${evidenceId}`, { method: 'DELETE' })
    if (res.ok) setEvidences((prev) => prev.filter((e) => e.id !== evidenceId))
  }

  const sevColor = SEVERITY_COLORS[incident.severity] || SEVERITY_COLORS.LOW
  const stColor = STATUS_COLORS[incident.status] || STATUS_COLORS.NEW

  return (
    <div style={{ padding: '24px', display: 'flex', gap: '24px' }}>
      {/* ── Left column ── */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Breadcrumb + PDF button */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
            <Link href="/incidents" style={{ color: '#3b82f6', textDecoration: 'none' }}>Incydenty</Link>
            {' › '}{incident.incidentNumber}
          </div>
          <a
            href={`/incidents/${incident.id}/print`}
            target="_blank"
            rel="noopener noreferrer"
            style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px', textDecoration: 'none' }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
            Raport PDF
          </a>
        </div>

        <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#e8eaf0', margin: '0 0 12px' }}>
          {incident.title}
        </h1>

        {/* Badges */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <Badge bg={sevColor.bg} text={sevColor.text} border={sevColor.border}>{SEVERITY_LABELS[incident.severity]}</Badge>
          <Badge bg={stColor.bg} text={stColor.text} border={stColor.border}>{STATUS_LABELS[incident.status]}</Badge>
          {incident.nis2Active && <Badge bg="rgba(245,158,11,0.15)" text="#fcd34d" border="rgba(245,158,11,0.25)">NIS2 Art. 21</Badge>}
          <Badge bg="rgba(59,130,246,0.1)" text="#93c5fd" border="rgba(59,130,246,0.2)">ISO A.6.8 · A.8.15</Badge>
        </div>

        {/* NIS2 Timer + Actions */}
        {incident.nis2Active && incident.nis2StartedAt && (
          <div style={{ marginBottom: '20px' }}>
            <NIS2Timer
              startedAt={incident.nis2StartedAt}
              earlyWarningSentAt={incident.nis2EarlyWarningSentAt}
              reportSentAt={incident.nis2ReportSentAt}
            />
            {/* NIS2 action buttons */}
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <Nis2Button
                label="Wyślij Early Warning (24h)"
                done={!!incident.nis2EarlyWarningSentAt}
                loading={nis2Loading === 'early_warning'}
                doneAt={incident.nis2EarlyWarningSentAt}
                onClick={() => sendNis2Action('early_warning')}
              />
              <Nis2Button
                label="Wyślij Raport 72h"
                done={!!incident.nis2ReportSentAt}
                loading={nis2Loading === 'report_72h'}
                doneAt={incident.nis2ReportSentAt}
                onClick={() => sendNis2Action('report_72h')}
                disabled={!incident.nis2EarlyWarningSentAt}
              />
              <Nis2Button
                label="Wyślij Raport końcowy"
                done={false}
                loading={nis2Loading === 'final_report'}
                doneAt={null}
                onClick={() => sendNis2Action('final_report')}
                disabled={!incident.nis2ReportSentAt}
                variant="ghost"
              />
            </div>
          </div>
        )}

        {/* Description */}
        <Section title="Opis zdarzenia">
          <p style={{ fontSize: '14px', color: '#8b90a0', lineHeight: 1.7, margin: 0 }}>
            {incident.description}
          </p>
        </Section>

        {/* Timeline */}
        <Section title="Oś czasu działań">
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {actions.map((action) => (
              <div key={action.id} style={{ padding: '12px 14px', background: '#0f1117', borderRadius: '6px', borderLeft: '2px solid rgba(59,130,246,0.3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontSize: '12px', color: '#3b82f6', fontWeight: 500 }}>{action.authorName}</span>
                  <span style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>{formatDate(action.createdAt)}</span>
                </div>
                <p style={{ fontSize: '13px', color: '#8b90a0', margin: 0, lineHeight: 1.6 }}>{action.content}</p>
              </div>
            ))}
          </div>

          {incident.status !== 'CLOSED' && (
            <div style={{ marginTop: '14px' }}>
              <textarea
                rows={3}
                value={newAction}
                onChange={(e) => setNewAction(e.target.value)}
                placeholder="Dodaj działanie, notatkę lub aktualizację..."
                style={{ width: '100%', padding: '10px 12px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', resize: 'vertical', boxSizing: 'border-box' }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
                <button
                  onClick={addAction}
                  disabled={savingAction || !newAction.trim()}
                  style={{ padding: '7px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', cursor: 'pointer', opacity: savingAction || !newAction.trim() ? 0.5 : 1 }}
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
                  Zatwierdź i zamknij incydent
                </button>
              )}
            </div>
          </Section>
        )}
      </div>

      {/* ── Right sidebar ── */}
      <div style={{ width: '290px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Details */}
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
                <Link href={`/assets/${asset.id}`} style={{ textDecoration: 'none' }}>
                  <div style={{ fontSize: '12px', color: '#93c5fd', fontWeight: 500 }}>{asset.name}</div>
                  <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
                    {asset.assetNumber} · {ASSET_TYPE_LABELS[asset.type]}
                  </div>
                </Link>
              </div>
            ))}
          </SideCard>
        )}

        {/* Evidence */}
        <SideCard title={`Dowody (${evidences.length})`}>
          <input
            ref={fileRef}
            type="file"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploadingFile || incident.status === 'CLOSED'}
            style={{
              width: '100%',
              padding: '7px',
              background: 'rgba(59,130,246,0.1)',
              color: '#93c5fd',
              border: '1px solid rgba(59,130,246,0.2)',
              borderRadius: '6px',
              fontSize: '12px',
              cursor: uploadingFile || incident.status === 'CLOSED' ? 'not-allowed' : 'pointer',
              marginBottom: '10px',
              opacity: incident.status === 'CLOSED' ? 0.5 : 1,
            }}
          >
            {uploadingFile ? 'Przesyłanie...' : '+ Załącz plik (max 50MB)'}
          </button>

          {evidences.length === 0 ? (
            <p style={{ fontSize: '12px', color: '#555b6e', margin: 0 }}>Brak załączonych dowodów</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {evidences.map((ev) => (
                <div key={ev.id} style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', padding: '8px', background: '#0f1117', borderRadius: '5px' }}>
                  <div style={{ minWidth: 0 }}>
                    {ev.downloadUrl ? (
                      <a href={ev.downloadUrl} target="_blank" rel="noopener noreferrer" style={{ fontSize: '12px', color: '#93c5fd', textDecoration: 'none', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.filename}
                      </a>
                    ) : (
                      <div style={{ fontSize: '12px', color: '#8b90a0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ev.filename}</div>
                    )}
                    <div style={{ fontSize: '10px', color: '#555b6e', marginTop: '2px', fontFamily: 'IBM Plex Mono, monospace' }}>
                      {formatFileSize(ev.size)} · {formatDate(ev.createdAt)}
                    </div>
                  </div>
                  {incident.status !== 'CLOSED' && (
                    <button
                      onClick={() => deleteEvidence(ev.id)}
                      style={{ marginLeft: '6px', background: 'transparent', border: 'none', color: '#555b6e', cursor: 'pointer', fontSize: '14px', padding: '0 2px', flexShrink: 0 }}
                      title="Usuń dowód"
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
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

/* ── NIS2 Button ─────────────────────────────── */
function Nis2Button({
  label, done, loading, doneAt, onClick, disabled, variant = 'default',
}: {
  label: string
  done: boolean
  loading: boolean
  doneAt: string | null
  onClick: () => void
  disabled?: boolean
  variant?: 'default' | 'ghost'
}) {
  if (done && doneAt) {
    return (
      <div style={{ padding: '6px 12px', background: 'rgba(34,197,94,0.1)', border: '1px solid rgba(34,197,94,0.2)', borderRadius: '6px', fontSize: '11px', color: '#86efac', fontFamily: 'IBM Plex Mono, monospace' }}>
        ✓ {label.split(' ').slice(1).join(' ')} — {formatDate(doneAt)}
      </div>
    )
  }
  return (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      style={{
        padding: '6px 12px',
        background: variant === 'ghost' ? 'transparent' : 'rgba(245,158,11,0.1)',
        border: `1px solid ${variant === 'ghost' ? 'rgba(255,255,255,0.1)' : 'rgba(245,158,11,0.25)'}`,
        borderRadius: '6px',
        fontSize: '11px',
        color: variant === 'ghost' ? '#8b90a0' : '#fcd34d',
        cursor: loading || disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        fontFamily: 'IBM Plex Mono, monospace',
      }}
    >
      {loading ? 'Wysyłanie...' : label}
    </button>
  )
}

/* ── Shared ──────────────────────────────────── */
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

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
