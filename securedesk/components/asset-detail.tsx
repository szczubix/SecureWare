'use client'

import { useState } from 'react'
import Link from 'next/link'
import { formatDate, formatDateShort, ASSET_TYPE_LABELS, CLASSIFICATION_LABELS, SEVERITY_LABELS, STATUS_LABELS } from '@/lib/utils'

interface HistoryEntry {
  id: string
  field: string
  oldValue: string | null
  newValue: string | null
  changedBy: string
  createdAt: string
}

interface RelatedIncident {
  id: string
  incidentNumber: string
  title: string
  severity: string
  status: string
  createdAt: string
}

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
  updatedAt: string
  history: HistoryEntry[]
  incidents: { incident: RelatedIncident }[]
}

const classColors: Record<string, { bg: string; text: string; border: string }> = {
  RESTRICTED: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  CONFIDENTIAL: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  INTERNAL: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
  PUBLIC: { bg: 'rgba(34,197,94,0.15)', text: '#86efac', border: 'rgba(34,197,94,0.25)' },
}

const sevColors: Record<string, { bg: string; text: string; border: string }> = {
  CRITICAL: { bg: 'rgba(239,68,68,0.15)', text: '#fca5a5', border: 'rgba(239,68,68,0.25)' },
  HIGH: { bg: 'rgba(249,115,22,0.15)', text: '#fdba74', border: 'rgba(249,115,22,0.25)' },
  MEDIUM: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
  LOW: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
}

const FIELD_LABELS: Record<string, string> = {
  name: 'Nazwa', type: 'Typ', classification: 'Klasyfikacja',
  description: 'Opis', location: 'Lokalizacja',
  businessOwner: 'Właściciel biznesowy', technicalOwner: 'Właściciel techniczny',
  nextReviewAt: 'Następny przegląd',
}

export function AssetDetail({ asset: initial, currentUser }: { asset: Asset; currentUser: { name: string } }) {
  const [asset, setAsset] = useState(initial)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveMsg, setSaveMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)
  const [form, setForm] = useState({
    name: initial.name,
    type: initial.type,
    classification: initial.classification,
    description: initial.description || '',
    location: initial.location || '',
    businessOwner: initial.businessOwner || '',
    technicalOwner: initial.technicalOwner || '',
    nextReviewAt: initial.nextReviewAt ? initial.nextReviewAt.slice(0, 10) : '',
  })

  const cc = classColors[asset.classification] || classColors.INTERNAL
  const isOverdue = asset.nextReviewAt && new Date(asset.nextReviewAt) < new Date()

  async function saveChanges() {
    setSaving(true)
    setSaveMsg(null)
    const res = await fetch(`/api/assets/${asset.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...form,
        nextReviewAt: form.nextReviewAt ? new Date(form.nextReviewAt).toISOString() : null,
        businessOwner: form.businessOwner || null,
        technicalOwner: form.technicalOwner || null,
      }),
    })
    if (res.ok) {
      const d = await res.json()
      setAsset((prev) => ({ ...prev, ...d.data }))
      setSaveMsg({ type: 'ok', text: 'Zmiany zapisane' })
      setEditing(false)
    } else {
      const d = await res.json()
      setSaveMsg({ type: 'err', text: typeof d.error === 'string' ? d.error : 'Błąd zapisu' })
    }
    setSaving(false)
  }

  return (
    <div style={{ padding: '24px', display: 'flex', gap: '24px' }}>
      {/* Left column */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Breadcrumb */}
        <div style={{ fontSize: '12px', color: '#555b6e', marginBottom: '16px', fontFamily: 'IBM Plex Mono, monospace' }}>
          <Link href="/assets" style={{ color: '#3b82f6', textDecoration: 'none' }}>Aktywa</Link>
          {' › '}{asset.assetNumber}
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h1 style={{ fontSize: '22px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>{asset.name}</h1>
          <button
            onClick={() => { setEditing(!editing); setSaveMsg(null) }}
            style={{ padding: '6px 14px', background: editing ? 'rgba(255,255,255,0.06)' : 'rgba(59,130,246,0.1)', color: editing ? '#8b90a0' : '#93c5fd', border: `1px solid ${editing ? 'rgba(255,255,255,0.1)' : 'rgba(59,130,246,0.2)'}`, borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
          >
            {editing ? 'Anuluj edycję' : 'Edytuj'}
          </button>
        </div>

        {/* Badges */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <span style={{ padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: cc.bg, color: cc.text, border: `1px solid ${cc.border}` }}>
            {CLASSIFICATION_LABELS[asset.classification]}
          </span>
          <span style={{ padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: 'rgba(255,255,255,0.06)', color: '#8b90a0', border: '1px solid rgba(255,255,255,0.1)' }}>
            {ASSET_TYPE_LABELS[asset.type]}
          </span>
          {isOverdue && (
            <span style={{ padding: '3px 10px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: 'rgba(245,158,11,0.15)', color: '#fcd34d', border: '1px solid rgba(245,158,11,0.25)' }}>
              ⚠ Przegląd przeterminowany
            </span>
          )}
        </div>

        {!editing ? (
          /* View mode */
          <div>
            <Section title="Dane aktywa">
              <Grid>
                <InfoRow label="Numer aktywa"><span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: '#3b82f6' }}>{asset.assetNumber}</span></InfoRow>
                <InfoRow label="Typ">{ASSET_TYPE_LABELS[asset.type]}</InfoRow>
                <InfoRow label="Klasyfikacja">{CLASSIFICATION_LABELS[asset.classification]}</InfoRow>
                <InfoRow label="Lokalizacja">{asset.location || <Dash />}</InfoRow>
                <InfoRow label="Właściciel biznesowy">{asset.businessOwner || <Dash />}</InfoRow>
                <InfoRow label="Właściciel techniczny">{asset.technicalOwner || <Dash />}</InfoRow>
                <InfoRow label="Następny przegląd">
                  {asset.nextReviewAt ? (
                    <span style={{ color: isOverdue ? '#fca5a5' : '#8b90a0' }}>
                      {formatDateShort(asset.nextReviewAt)}
                    </span>
                  ) : <Dash />}
                </InfoRow>
                <InfoRow label="Zarejestrowano">{formatDateShort(asset.createdAt)}</InfoRow>
              </Grid>
              {asset.description && (
                <div style={{ marginTop: '16px', padding: '12px', background: '#0f1117', borderRadius: '6px' }}>
                  <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', marginBottom: '6px' }}>Opis</div>
                  <p style={{ fontSize: '13px', color: '#8b90a0', margin: 0, lineHeight: 1.7 }}>{asset.description}</p>
                </div>
              )}
            </Section>

            {/* Save message after edit */}
            {saveMsg && (
              <div style={{ padding: '10px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '16px', background: saveMsg.type === 'ok' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${saveMsg.type === 'ok' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`, color: saveMsg.type === 'ok' ? '#86efac' : '#fca5a5' }}>
                {saveMsg.text}
              </div>
            )}
          </div>
        ) : (
          /* Edit mode */
          <Section title="Edycja aktywa">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
              <EditField label="Nazwa">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={inputStyle} />
              </EditField>
              <EditField label="Typ">
                <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} style={inputStyle}>
                  <option value="HARDWARE">Sprzęt</option>
                  <option value="SOFTWARE">Oprogramowanie</option>
                  <option value="DATA">Dane</option>
                  <option value="CLOUD_SERVICE">Usługa cloud</option>
                  <option value="INFRASTRUCTURE">Infrastruktura</option>
                  <option value="OTHER">Inne</option>
                </select>
              </EditField>
              <EditField label="Klasyfikacja">
                <select value={form.classification} onChange={(e) => setForm({ ...form, classification: e.target.value })} style={inputStyle}>
                  <option value="PUBLIC">Publiczny</option>
                  <option value="INTERNAL">Wewnętrzny</option>
                  <option value="CONFIDENTIAL">Poufny</option>
                  <option value="RESTRICTED">Zastrzeżony</option>
                </select>
              </EditField>
              <EditField label="Lokalizacja">
                <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} style={inputStyle} placeholder="Np. serwerownia, chmura" />
              </EditField>
              <EditField label="Właściciel biznesowy">
                <input value={form.businessOwner} onChange={(e) => setForm({ ...form, businessOwner: e.target.value })} style={inputStyle} />
              </EditField>
              <EditField label="Właściciel techniczny">
                <input value={form.technicalOwner} onChange={(e) => setForm({ ...form, technicalOwner: e.target.value })} style={inputStyle} />
              </EditField>
              <EditField label="Następny przegląd (data)">
                <input type="date" value={form.nextReviewAt} onChange={(e) => setForm({ ...form, nextReviewAt: e.target.value })} style={inputStyle} />
              </EditField>
            </div>
            <EditField label="Opis" style={{ marginBottom: '14px' }}>
              <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} style={{ ...inputStyle, resize: 'vertical' }} />
            </EditField>

            {saveMsg && (
              <div style={{ padding: '10px 12px', borderRadius: '6px', fontSize: '12px', marginBottom: '14px', background: saveMsg.type === 'ok' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)', border: `1px solid ${saveMsg.type === 'ok' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`, color: saveMsg.type === 'ok' ? '#86efac' : '#fca5a5' }}>
                {saveMsg.text}
              </div>
            )}
            <button onClick={saveChanges} disabled={saving} style={{ padding: '8px 18px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: saving ? 0.7 : 1 }}>
              {saving ? 'Zapisywanie...' : 'Zapisz zmiany'}
            </button>
          </Section>
        )}

        {/* Change history */}
        <Section title={`Historia zmian (${asset.history.length})`}>
          {asset.history.length === 0 ? (
            <p style={{ fontSize: '13px', color: '#555b6e' }}>Brak zarejestrowanych zmian</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {asset.history.map((h) => (
                <div key={h.id} style={{ padding: '10px 12px', background: '#161922', borderRadius: '6px', borderLeft: '2px solid rgba(59,130,246,0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '12px', color: '#3b82f6' }}>{h.changedBy}</span>
                    <span style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>{formatDate(h.createdAt)}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#8b90a0' }}>
                    <span style={{ color: '#555b6e' }}>{FIELD_LABELS[h.field] || h.field}:</span>
                    {' '}
                    <span style={{ color: '#fca5a5', textDecoration: 'line-through', marginRight: '6px' }}>{h.oldValue || '—'}</span>
                    <span style={{ color: '#86efac' }}>→ {h.newValue || '—'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>

      {/* Right sidebar */}
      <div style={{ width: '260px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {/* Related incidents */}
        <SideCard title={`Incydenty (${asset.incidents.length})`}>
          {asset.incidents.length === 0 ? (
            <p style={{ fontSize: '12px', color: '#555b6e', margin: 0 }}>Brak powiązanych incydentów</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {asset.incidents.map(({ incident }) => {
                const sc = sevColors[incident.severity] || sevColors.LOW
                return (
                  <Link key={incident.id} href={`/incidents/${incident.id}`} style={{ textDecoration: 'none', display: 'block', padding: '8px', background: '#0f1117', borderRadius: '5px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                      <span style={{ fontSize: '11px', color: '#3b82f6', fontFamily: 'IBM Plex Mono, monospace' }}>{incident.incidentNumber}</span>
                      <span style={{ padding: '1px 6px', borderRadius: '3px', fontSize: '10px', background: sc.bg, color: sc.text, border: `1px solid ${sc.border}`, fontFamily: 'IBM Plex Mono, monospace' }}>
                        {SEVERITY_LABELS[incident.severity]}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#8b90a0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{incident.title}</div>
                    <div style={{ fontSize: '10px', color: '#555b6e', marginTop: '2px' }}>{STATUS_LABELS[incident.status]} · {formatDateShort(incident.createdAt)}</div>
                  </Link>
                )
              })}
            </div>
          )}
        </SideCard>

        {/* Quick info */}
        <SideCard title="Metadane">
          <InfoRow label="ID"><span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '10px', wordBreak: 'break-all' }}>{asset.id}</span></InfoRow>
          <InfoRow label="Utworzono">{formatDateShort(asset.createdAt)}</InfoRow>
          <InfoRow label="Zaktualizowano">{formatDateShort(asset.updatedAt)}</InfoRow>
        </SideCard>

        <Link href="/assets" style={{ display: 'block', padding: '8px', background: 'rgba(255,255,255,0.04)', color: '#8b90a0', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px', fontSize: '12px', textDecoration: 'none', textAlign: 'center' }}>
          ← Powrót do listy
        </Link>
      </div>
    </div>
  )
}

/* ── Shared ──────────────────────────────────── */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ fontSize: '12px', fontFamily: 'IBM Plex Mono, monospace', color: '#555b6e', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 12px' }}>{title}</h3>
      {children}
    </div>
  )
}

function SideCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
      <h4 style={{ fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', color: '#555b6e', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 12px' }}>{title}</h4>
      {children}
    </div>
  )
}

function Grid({ children }: { children: React.ReactNode }) {
  return <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0' }}>{children}</div>
}

function InfoRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '3px' }}>{label}</div>
      <div style={{ fontSize: '13px', color: '#8b90a0' }}>{children}</div>
    </div>
  )
}

function EditField({ label, children, style }: { label: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={style}>
      <label style={{ display: 'block', fontSize: '11px', color: '#555b6e', marginBottom: '4px', fontFamily: 'IBM Plex Mono, monospace' }}>{label}</label>
      {children}
    </div>
  )
}

function Dash() {
  return <span style={{ color: '#3a3f52' }}>—</span>
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '7px 10px',
  background: '#0f1117',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '5px',
  color: '#e8eaf0',
  fontSize: '13px',
  outline: 'none',
  boxSizing: 'border-box',
}
