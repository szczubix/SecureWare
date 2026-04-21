'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { formatDateShort } from '@/lib/utils'

interface Asset { id: string; assetNumber: string; name: string; type: string }
interface Risk {
  id: string
  riskNumber: string
  title: string
  description: string
  threat: string | null
  vulnerability: string | null
  category: string
  probability: number
  impact: number
  riskScore: number
  treatment: string
  status: string
  owner: string
  mitigationPlan: string | null
  residualProb: number | null
  residualImpact: number | null
  residualScore: number | null
  nextReviewAt: string | null
  closedAt: string | null
  createdAt: string
  updatedAt: string
  assets: { asset: Asset }[]
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

function scoreLevel(s: number | null): { label: string; color: string; bg: string; border: string } {
  if (!s) return { label: '—', color: '#555b6e', bg: 'transparent', border: 'transparent' }
  if (s >= 15) return { label: 'Krytyczne', color: '#fca5a5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)' }
  if (s >= 10) return { label: 'Wysokie',   color: '#fdba74', bg: 'rgba(249,115,22,0.15)', border: 'rgba(249,115,22,0.3)' }
  if (s >= 5)  return { label: 'Średnie',   color: '#fcd34d', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)' }
  return             { label: 'Niskie',    color: '#86efac', bg: 'rgba(34,197,94,0.15)',  border: 'rgba(34,197,94,0.3)' }
}

function ScoreBadge({ score }: { score: number | null }) {
  if (!score) return <span style={{ color: '#3a3f52', fontSize: '13px' }}>—</span>
  const lvl = scoreLevel(score)
  return (
    <span style={{ padding: '3px 12px', borderRadius: '4px', fontSize: '13px', fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, background: lvl.bg, color: lvl.color, border: `1px solid ${lvl.border}` }}>
      {score} · {lvl.label}
    </span>
  )
}

function ScaleBtn({ val, current, set, disabled }: { val: number; current: number; set: (v: number) => void; disabled?: boolean }) {
  return (
    <button type="button" onClick={() => !disabled && set(val)} disabled={disabled}
      style={{ width: '32px', height: '32px', borderRadius: '6px', border: current === val ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)', background: current === val ? 'rgba(59,130,246,0.2)' : '#0f1117', color: current === val ? '#93c5fd' : '#555b6e', fontSize: '13px', fontWeight: 600, cursor: disabled ? 'default' : 'pointer' }}>{val}</button>
  )
}

export function RiskDetail({ risk: initial, currentUser }: { risk: Risk; currentUser: { name: string } }) {
  const router = useRouter()
  const [risk, setRisk] = useState<Risk>(initial)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    title: risk.title,
    description: risk.description,
    threat: risk.threat || '',
    vulnerability: risk.vulnerability || '',
    category: risk.category,
    probability: risk.probability,
    impact: risk.impact,
    treatment: risk.treatment,
    status: risk.status,
    owner: risk.owner,
    mitigationPlan: risk.mitigationPlan || '',
    residualProb: risk.residualProb ?? ('' as number | ''),
    residualImpact: risk.residualImpact ?? ('' as number | ''),
    nextReviewAt: risk.nextReviewAt ? risk.nextReviewAt.slice(0, 10) : '',
  })

  const editScore = form.probability * form.impact
  const editResScore = (typeof form.residualProb === 'number' && typeof form.residualImpact === 'number')
    ? form.residualProb * form.residualImpact
    : null

  async function handleSave() {
    setSaving(true); setError('')
    const body: Record<string, unknown> = {
      ...form,
      threat: form.threat || null,
      vulnerability: form.vulnerability || null,
      mitigationPlan: form.mitigationPlan || null,
      residualProb: typeof form.residualProb === 'number' ? form.residualProb : null,
      residualImpact: typeof form.residualImpact === 'number' ? form.residualImpact : null,
      nextReviewAt: form.nextReviewAt ? new Date(form.nextReviewAt).toISOString() : null,
    }
    const res = await fetch(`/api/risks/${risk.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (res.ok) {
      const { data } = await res.json()
      setRisk(data)
      setEditing(false)
    } else {
      const d = await res.json()
      setError(d.error?.formErrors?.[0] || 'Błąd zapisu')
    }
    setSaving(false)
  }

  async function handleDelete() {
    if (!confirm(`Usunąć ryzyko ${risk.riskNumber}? Operacja jest nieodwracalna.`)) return
    setDeleting(true)
    await fetch(`/api/risks/${risk.id}`, { method: 'DELETE' })
    router.push('/risks')
  }

  const iStyle: React.CSSProperties = { width: '100%', padding: '8px 10px', background: '#0f1117', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#e8eaf0', fontSize: '13px', outline: 'none', boxSizing: 'border-box' }
  const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
    <div>
      <label style={{ display: 'block', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '5px' }}>{label}</label>
      {children}
    </div>
  )

  return (
    <div style={{ padding: '24px', flex: 1, minWidth: 0 }}>
      {/* Breadcrumb */}
      <div style={{ fontSize: '12px', color: '#555b6e', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <Link href="/risks" style={{ color: '#3b82f6', textDecoration: 'none' }}>Rejestr ryzyk</Link>
        <span>/</span>
        <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{risk.riskNumber}</span>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '24px', gap: '16px' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px', flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '13px', color: '#3b82f6' }}>{risk.riskNumber}</span>
            <ScoreBadge score={risk.riskScore} />
            <span style={{ fontSize: '12px', color: '#8b90a0' }}>{STATUS_PL[risk.status] || risk.status}</span>
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>{risk.title}</h1>
          <p style={{ fontSize: '12px', color: '#555b6e', margin: '6px 0 0', fontFamily: 'IBM Plex Mono, monospace' }}>
            {CATEGORY_PL[risk.category]} · {TREATMENT_PL[risk.treatment]} · właściciel: {risk.owner}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
          {!editing && (
            <>
              <button onClick={() => setEditing(true)} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>
                Edytuj
              </button>
              <button onClick={handleDelete} disabled={deleting} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '6px', color: '#fca5a5', fontSize: '13px', cursor: 'pointer', opacity: deleting ? 0.5 : 1 }}>
                {deleting ? '...' : 'Usuń'}
              </button>
            </>
          )}
          {editing && (
            <>
              <button onClick={() => { setEditing(false); setError('') }} style={{ padding: '8px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '13px', cursor: 'pointer' }}>
                Anuluj
              </button>
              <button onClick={handleSave} disabled={saving} style={{ padding: '8px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: 'pointer', opacity: saving ? 0.7 : 1 }}>
                {saving ? 'Zapisywanie...' : 'Zapisz zmiany'}
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '16px', padding: '10px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: '6px', color: '#fca5a5', fontSize: '12px' }}>{error}</div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', alignItems: 'start' }}>
        {/* Main content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* Description */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
            <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>Opis ryzyka</div>
            {editing ? (
              <textarea rows={3} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} style={{ ...iStyle, resize: 'vertical' }} />
            ) : (
              <p style={{ margin: 0, fontSize: '13px', color: '#c8ccd6', lineHeight: 1.6 }}>{risk.description}</p>
            )}
          </div>

          {/* Threat & Vulnerability */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Zagrożenie (Threat)</div>
                {editing ? (
                  <input value={form.threat} onChange={e => setForm({ ...form, threat: e.target.value })} placeholder="Źródło zagrożenia..." style={iStyle} />
                ) : (
                  <p style={{ margin: 0, fontSize: '13px', color: risk.threat ? '#c8ccd6' : '#3a3f52', fontStyle: risk.threat ? 'normal' : 'italic' }}>{risk.threat || 'Nie określono'}</p>
                )}
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>Podatność (Vulnerability)</div>
                {editing ? (
                  <input value={form.vulnerability} onChange={e => setForm({ ...form, vulnerability: e.target.value })} placeholder="Wykorzystywana słabość..." style={iStyle} />
                ) : (
                  <p style={{ margin: 0, fontSize: '13px', color: risk.vulnerability ? '#c8ccd6' : '#3a3f52', fontStyle: risk.vulnerability ? 'normal' : 'italic' }}>{risk.vulnerability || 'Nie określono'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Risk score */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
            <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>Ocena ryzyka</div>
            {editing ? (
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Prawdopodobieństwo</div>
                  <div style={{ display: 'flex', gap: '4px' }}>{[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={form.probability} set={v2 => setForm({...form, probability: v2})} />)}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Wpływ</div>
                  <div style={{ display: 'flex', gap: '4px' }}>{[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={form.impact} set={v2 => setForm({...form, impact: v2})} />)}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wynik</div>
                  <div style={{ fontSize: '28px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: scoreLevel(editScore).color }}>{editScore}</div>
                  <div style={{ fontSize: '11px', color: scoreLevel(editScore).color }}>{scoreLevel(editScore).label}</div>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Prawdopodobieństwo</div>
                  <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: '#e8eaf0' }}>{risk.probability}</div>
                </div>
                <div style={{ fontSize: '20px', color: '#3a3f52', alignSelf: 'center', marginTop: '16px' }}>×</div>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wpływ</div>
                  <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: '#e8eaf0' }}>{risk.impact}</div>
                </div>
                <div style={{ fontSize: '20px', color: '#3a3f52', alignSelf: 'center', marginTop: '16px' }}>=</div>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wynik ryzyka</div>
                  <ScoreBadge score={risk.riskScore} />
                </div>
              </div>
            )}
          </div>

          {/* Residual risk */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
            <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>Ryzyko rezydualne (po mitigacji)</div>
            {editing ? (
              <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Prawdop. rezydualne</div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button type="button" onClick={() => setForm({...form, residualProb: '', residualImpact: ''})}
                      style={{ height: '32px', padding: '0 8px', borderRadius: '6px', border: form.residualProb === '' ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)', background: form.residualProb === '' ? 'rgba(59,130,246,0.2)' : '#0f1117', color: '#555b6e', fontSize: '11px', cursor: 'pointer' }}>—</button>
                    {[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={typeof form.residualProb === 'number' ? form.residualProb : 0} set={v2 => setForm({...form, residualProb: v2})} />)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '6px' }}>Wpływ rezydualny</div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    <button type="button" onClick={() => setForm({...form, residualProb: '', residualImpact: ''})}
                      style={{ height: '32px', padding: '0 8px', borderRadius: '6px', border: form.residualImpact === '' ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)', background: form.residualImpact === '' ? 'rgba(59,130,246,0.2)' : '#0f1117', color: '#555b6e', fontSize: '11px', cursor: 'pointer' }}>—</button>
                    {[1,2,3,4,5].map(v => <ScaleBtn key={v} val={v} current={typeof form.residualImpact === 'number' ? form.residualImpact : 0} set={v2 => setForm({...form, residualImpact: v2})} />)}
                  </div>
                </div>
                {editResScore !== null && (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wynik</div>
                    <div style={{ fontSize: '28px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: scoreLevel(editResScore).color }}>{editResScore}</div>
                    <div style={{ fontSize: '11px', color: scoreLevel(editResScore).color }}>{scoreLevel(editResScore).label}</div>
                  </div>
                )}
              </div>
            ) : (
              <div>
                {risk.residualScore !== null ? (
                  <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Prawdop. rezydualne</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: '#e8eaf0' }}>{risk.residualProb}</div>
                    </div>
                    <div style={{ fontSize: '20px', color: '#3a3f52', alignSelf: 'center', marginTop: '16px' }}>×</div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wpływ rezydualny</div>
                      <div style={{ fontSize: '24px', fontWeight: 700, fontFamily: 'IBM Plex Mono, monospace', color: '#e8eaf0' }}>{risk.residualImpact}</div>
                    </div>
                    <div style={{ fontSize: '20px', color: '#3a3f52', alignSelf: 'center', marginTop: '16px' }}>=</div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#555b6e', marginBottom: '4px' }}>Wynik rezydualny</div>
                      <ScoreBadge score={risk.residualScore} />
                    </div>
                  </div>
                ) : (
                  <p style={{ margin: 0, fontSize: '13px', color: '#3a3f52', fontStyle: 'italic' }}>Nie określono ryzyka rezydualnego</p>
                )}
              </div>
            )}
          </div>

          {/* Mitigation plan */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
            <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>Plan mitigacji</div>
            {editing ? (
              <textarea rows={4} value={form.mitigationPlan} onChange={e => setForm({ ...form, mitigationPlan: e.target.value })} placeholder="Opisz planowane działania zaradcze..." style={{ ...iStyle, resize: 'vertical' }} />
            ) : (
              <p style={{ margin: 0, fontSize: '13px', color: risk.mitigationPlan ? '#c8ccd6' : '#3a3f52', fontStyle: risk.mitigationPlan ? 'normal' : 'italic', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{risk.mitigationPlan || 'Brak planu mitigacji'}</p>
            )}
          </div>

          {/* Related assets */}
          {risk.assets.length > 0 && (
            <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px' }}>
              <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>Powiązane aktywa</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {risk.assets.map(({ asset }) => (
                  <Link key={asset.id} href={`/assets/${asset.id}`} style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px', color: '#3b82f6' }}>{asset.assetNumber}</span>
                    <span style={{ fontSize: '12px', color: '#c8ccd6' }}>{asset.name}</span>
                    <span style={{ fontSize: '11px', color: '#555b6e', marginLeft: 'auto' }}>{asset.type}</span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

          {/* Status & treatment */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
            <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>Szczegóły</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Field label="Status">
                {editing ? (
                  <select value={form.status} onChange={e => setForm({ ...form, status: e.target.value })} style={{ ...iStyle, width: 'auto' }}>
                    <option value="OPEN">Otwarte</option>
                    <option value="IN_TREATMENT">W trakcie</option>
                    <option value="ACCEPTED">Zaakceptowane</option>
                    <option value="CLOSED">Zamknięte</option>
                  </select>
                ) : (
                  <span style={{ fontSize: '13px', color: '#e8eaf0' }}>{STATUS_PL[risk.status] || risk.status}</span>
                )}
              </Field>
              <Field label="Podejście">
                {editing ? (
                  <select value={form.treatment} onChange={e => setForm({ ...form, treatment: e.target.value })} style={{ ...iStyle, width: 'auto' }}>
                    <option value="MITIGATE">Mitigacja</option>
                    <option value="ACCEPT">Akceptacja</option>
                    <option value="TRANSFER">Transfer</option>
                    <option value="AVOID">Unikanie</option>
                  </select>
                ) : (
                  <span style={{ fontSize: '13px', color: '#e8eaf0' }}>{TREATMENT_PL[risk.treatment] || risk.treatment}</span>
                )}
              </Field>
              <Field label="Kategoria">
                {editing ? (
                  <select value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} style={{ ...iStyle, width: 'auto' }}>
                    <option value="CONFIDENTIALITY">Poufność</option>
                    <option value="INTEGRITY">Integralność</option>
                    <option value="AVAILABILITY">Dostępność</option>
                    <option value="PHYSICAL">Fizyczne</option>
                    <option value="LEGAL">Prawne</option>
                    <option value="OTHER">Inne</option>
                  </select>
                ) : (
                  <span style={{ fontSize: '13px', color: '#e8eaf0' }}>{CATEGORY_PL[risk.category] || risk.category}</span>
                )}
              </Field>
              <Field label="Właściciel ryzyka">
                {editing ? (
                  <input value={form.owner} onChange={e => setForm({ ...form, owner: e.target.value })} style={iStyle} />
                ) : (
                  <span style={{ fontSize: '13px', color: '#e8eaf0' }}>{risk.owner}</span>
                )}
              </Field>
              <Field label="Następny przegląd">
                {editing ? (
                  <input type="date" value={form.nextReviewAt} onChange={e => setForm({ ...form, nextReviewAt: e.target.value })} style={iStyle} />
                ) : (
                  <span style={{ fontSize: '13px', color: risk.nextReviewAt && new Date(risk.nextReviewAt) < new Date() ? '#fca5a5' : '#e8eaf0' }}>
                    {risk.nextReviewAt ? formatDateShort(risk.nextReviewAt) : '—'}
                    {risk.nextReviewAt && new Date(risk.nextReviewAt) < new Date() && <span style={{ fontSize: '11px', marginLeft: '6px', color: '#fca5a5' }}>⚠ przeterminowany</span>}
                  </span>
                )}
              </Field>
              {risk.closedAt && (
                <Field label="Zamknięto">
                  <span style={{ fontSize: '13px', color: '#8b90a0' }}>{formatDateShort(risk.closedAt)}</span>
                </Field>
              )}
            </div>
          </div>

          {/* Dates */}
          <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>
                <div style={{ fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '2px' }}>UTWORZONO</div>
                <div style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>{formatDateShort(risk.createdAt)}</div>
              </div>
              <div>
                <div style={{ fontSize: '10px', color: '#3a3f52', fontFamily: 'IBM Plex Mono, monospace', marginBottom: '2px' }}>AKTUALIZACJA</div>
                <div style={{ fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>{formatDateShort(risk.updatedAt)}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
