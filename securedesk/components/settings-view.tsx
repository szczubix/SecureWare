'use client'

import { useState, useEffect } from 'react'
import { formatDateShort } from '@/lib/utils'

interface UserInfo {
  id: string
  email: string
  name: string
  role: string
}

interface OrgInfo {
  id: string
  name: string
  plan: string
  createdAt: string
  _count: { users: number; incidents: number; assets: number }
}

interface Member {
  id: string
  email: string
  name: string | null
  role: string
  createdAt: string
}

const ROLE_LABELS: Record<string, string> = {
  OWNER: 'Właściciel',
  ABSI: 'ABSI',
  READONLY: 'Tylko odczyt',
}

const PLAN_LABELS: Record<string, { label: string; color: string }> = {
  STARTER: { label: 'Starter', color: '#8b90a0' },
  STANDARD: { label: 'Standard', color: '#3b82f6' },
  PRO: { label: 'Pro', color: '#f59e0b' },
}

type Tab = 'profile' | 'password' | 'organization' | 'members'

export function SettingsView({ user }: { user: UserInfo }) {
  const [tab, setTab] = useState<Tab>('profile')
  const [org, setOrg] = useState<OrgInfo | null>(null)
  const [members, setMembers] = useState<Member[]>([])

  useEffect(() => {
    fetch('/api/settings/organization')
      .then((r) => r.json())
      .then((d) => setOrg(d.data))
  }, [])

  useEffect(() => {
    if (tab === 'members') {
      fetch('/api/settings/members')
        .then((r) => r.json())
        .then((d) => setMembers(d.data || []))
    }
  }, [tab])

  const tabs: { key: Tab; label: string; ownerOnly?: boolean }[] = [
    { key: 'profile', label: 'Mój profil' },
    { key: 'password', label: 'Zmiana hasła' },
    { key: 'organization', label: 'Organizacja', ownerOnly: true },
    { key: 'members', label: 'Użytkownicy', ownerOnly: true },
  ]

  const visibleTabs = tabs.filter((t) => !t.ownerOnly || user.role === 'OWNER')

  return (
    <div style={{ padding: '24px', maxWidth: '800px' }}>
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '20px', fontWeight: 600, color: '#e8eaf0', margin: 0 }}>Ustawienia</h1>
        <p style={{ fontSize: '13px', color: '#555b6e', margin: '4px 0 0' }}>
          Zarządzaj profilem, hasłem i organizacją
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '2px', marginBottom: '24px', borderBottom: '1px solid rgba(255,255,255,0.07)', paddingBottom: '0' }}>
        {visibleTabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              background: 'transparent',
              border: 'none',
              borderBottom: tab === t.key ? '2px solid #3b82f6' : '2px solid transparent',
              color: tab === t.key ? '#e8eaf0' : '#8b90a0',
              cursor: 'pointer',
              marginBottom: '-1px',
              fontWeight: tab === t.key ? 500 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profile' && <ProfileTab user={user} />}
      {tab === 'password' && <PasswordTab />}
      {tab === 'organization' && <OrganizationTab org={org} onUpdate={setOrg} />}
      {tab === 'members' && <MembersTab members={members} currentUserId={user.id} onRefresh={() => fetch('/api/settings/members').then(r => r.json()).then(d => setMembers(d.data || []))} />}
    </div>
  )
}

/* ─── Profile Tab ─────────────────────────────── */
function ProfileTab({ user }: { user: UserInfo }) {
  const [name, setName] = useState(user.name)
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  const planInfo = PLAN_LABELS['STARTER']

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    const res = await fetch('/api/settings/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (res.ok) {
      setMsg({ type: 'ok', text: 'Profil zaktualizowany. Zmiany będą widoczne po ponownym zalogowaniu.' })
    } else {
      const d = await res.json()
      setMsg({ type: 'err', text: d.error?.formErrors?.[0] || 'Błąd zapisu' })
    }
    setSaving(false)
  }

  return (
    <div>
      <Card title="Dane konta">
        {/* Role + plan badge row */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <InfoBadge label="Rola">{ROLE_LABELS[user.role] || user.role}</InfoBadge>
          <InfoBadge label="Plan">{planInfo.label}</InfoBadge>
        </div>

        <form onSubmit={save}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
            <FormField label="Imię i nazwisko">
              <input
                required
                minLength={2}
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={inputStyle}
              />
            </FormField>
            <FormField label="Adres email">
              <input
                value={user.email}
                disabled
                style={{ ...inputStyle, opacity: 0.5, cursor: 'not-allowed' }}
              />
            </FormField>
          </div>
          <Alert msg={msg} />
          <SaveButton loading={saving}>Zapisz profil</SaveButton>
        </form>
      </Card>

      <Card title="Informacje o sesji" style={{ marginTop: '16px' }}>
        <Row label="ID użytkownika"><Mono>{user.id}</Mono></Row>
        <Row label="Email">{user.email}</Row>
        <Row label="Rola w systemie">{ROLE_LABELS[user.role] || user.role}</Row>
      </Card>
    </div>
  )
}

/* ─── Password Tab ────────────────────────────── */
function PasswordTab() {
  const [form, setForm] = useState({ currentPassword: '', newPassword: '', confirm: '' })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  async function save(e: React.FormEvent) {
    e.preventDefault()
    if (form.newPassword !== form.confirm) {
      setMsg({ type: 'err', text: 'Nowe hasła nie są identyczne' })
      return
    }
    setSaving(true)
    setMsg(null)
    const res = await fetch('/api/settings/password', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ currentPassword: form.currentPassword, newPassword: form.newPassword }),
    })
    if (res.ok) {
      setMsg({ type: 'ok', text: 'Hasło zostało zmienione pomyślnie' })
      setForm({ currentPassword: '', newPassword: '', confirm: '' })
    } else {
      const d = await res.json()
      setMsg({ type: 'err', text: typeof d.error === 'string' ? d.error : d.error?.formErrors?.[0] || 'Błąd' })
    }
    setSaving(false)
  }

  return (
    <Card title="Zmiana hasła">
      <form onSubmit={save}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '380px' }}>
          <FormField label="Aktualne hasło">
            <input
              type="password"
              required
              value={form.currentPassword}
              onChange={(e) => setForm({ ...form, currentPassword: e.target.value })}
              style={inputStyle}
            />
          </FormField>
          <FormField label="Nowe hasło">
            <input
              type="password"
              required
              minLength={8}
              value={form.newPassword}
              onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
              placeholder="Min. 8 znaków"
              style={inputStyle}
            />
          </FormField>
          <FormField label="Powtórz nowe hasło">
            <input
              type="password"
              required
              value={form.confirm}
              onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              style={inputStyle}
            />
          </FormField>
        </div>
        <Alert msg={msg} style={{ marginTop: '14px', maxWidth: '380px' }} />
        <SaveButton loading={saving} style={{ marginTop: '16px' }}>Zmień hasło</SaveButton>
      </form>
    </Card>
  )
}

/* ─── Organization Tab ────────────────────────── */
function OrganizationTab({ org, onUpdate }: { org: OrgInfo | null; onUpdate: (o: OrgInfo) => void }) {
  const [name, setName] = useState(org?.name || '')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => { if (org) setName(org.name) }, [org])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    const res = await fetch('/api/settings/organization', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (res.ok) {
      const d = await res.json()
      onUpdate({ ...org!, ...d.data })
      setMsg({ type: 'ok', text: 'Nazwa organizacji zaktualizowana' })
    } else {
      const d = await res.json()
      setMsg({ type: 'err', text: typeof d.error === 'string' ? d.error : 'Błąd zapisu' })
    }
    setSaving(false)
  }

  if (!org) return <div style={{ color: '#555b6e', fontSize: '13px' }}>Ładowanie...</div>

  const plan = PLAN_LABELS[org.plan] || PLAN_LABELS.STARTER

  return (
    <div>
      <Card title="Dane organizacji">
        <form onSubmit={save}>
          <FormField label="Nazwa organizacji" style={{ maxWidth: '420px', marginBottom: '14px' }}>
            <input
              required
              minLength={2}
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={inputStyle}
            />
          </FormField>
          <Alert msg={msg} style={{ maxWidth: '420px' }} />
          <SaveButton loading={saving} style={{ marginTop: '14px' }}>Zapisz nazwę</SaveButton>
        </form>
      </Card>

      <Card title="Statystyki i plan" style={{ marginTop: '16px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '16px' }}>
          {[
            { label: 'Użytkownicy', value: org._count.users },
            { label: 'Incydenty', value: org._count.incidents },
            { label: 'Aktywa', value: org._count.assets },
          ].map((s) => (
            <div key={s.label} style={{ background: '#0f1117', borderRadius: '6px', padding: '14px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 600, color: '#e8eaf0', fontFamily: 'IBM Plex Mono, monospace' }}>
                {s.value}
              </div>
              <div style={{ fontSize: '11px', color: '#555b6e', marginTop: '4px' }}>{s.label}</div>
            </div>
          ))}
        </div>
        <Row label="Plan">
          <span style={{ color: plan.color, fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px' }}>
            ● {plan.label}
          </span>
        </Row>
        <Row label="ID organizacji"><Mono>{org.id}</Mono></Row>
        <Row label="Utworzona">{formatDateShort(org.createdAt)}</Row>
      </Card>
    </div>
  )
}

/* ─── Members Tab ─────────────────────────────── */
function MembersTab({ members, currentUserId, onRefresh }: { members: Member[]; currentUserId: string; onRefresh: () => void }) {
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ email: '', name: '', role: 'ABSI', password: '' })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ type: 'ok' | 'err'; text: string } | null>(null)

  async function invite(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    const res = await fetch('/api/settings/members', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })
    if (res.ok) {
      setMsg({ type: 'ok', text: 'Użytkownik dodany pomyślnie' })
      setForm({ email: '', name: '', role: 'ABSI', password: '' })
      setShowForm(false)
      onRefresh()
    } else {
      const d = await res.json()
      setMsg({ type: 'err', text: typeof d.error === 'string' ? d.error : d.error?.formErrors?.[0] || 'Błąd' })
    }
    setSaving(false)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '14px', color: '#e8eaf0' }}>
          Użytkownicy ({members.length})
        </h3>
        <button
          onClick={() => setShowForm(!showForm)}
          style={{ padding: '7px 14px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
        >
          + Dodaj użytkownika
        </button>
      </div>

      {showForm && (
        <Card title="Nowy użytkownik" style={{ marginBottom: '16px' }}>
          <form onSubmit={invite}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
              <FormField label="Imię i nazwisko">
                <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} style={inputStyle} placeholder="Jan Kowalski" />
              </FormField>
              <FormField label="Email">
                <input type="email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={inputStyle} placeholder="jan@firma.pl" />
              </FormField>
              <FormField label="Rola">
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} style={inputStyle}>
                  <option value="ABSI">ABSI</option>
                  <option value="READONLY">Tylko odczyt</option>
                  <option value="OWNER">Właściciel</option>
                </select>
              </FormField>
              <FormField label="Hasło tymczasowe">
                <input type="password" required minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={inputStyle} placeholder="Min. 8 znaków" />
              </FormField>
            </div>
            <Alert msg={msg} />
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <SaveButton loading={saving}>Dodaj użytkownika</SaveButton>
              <button type="button" onClick={() => setShowForm(false)} style={{ padding: '7px 14px', background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '6px', color: '#8b90a0', fontSize: '12px', cursor: 'pointer' }}>
                Anuluj
              </button>
            </div>
          </form>
        </Card>
      )}

      <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
              {['Użytkownik', 'Rola', 'Dołączył/a', ''].map((col) => (
                <th key={col} style={{ padding: '10px 16px', textAlign: 'left', fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {members.map((m) => (
              <tr key={m.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500 }}>{m.name || '—'}</div>
                  <div style={{ fontSize: '11px', color: '#555b6e', marginTop: '2px' }}>{m.email}</div>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <RoleBadge role={m.role} />
                </td>
                <td style={{ padding: '12px 16px', fontSize: '12px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace' }}>
                  {formatDateShort(m.createdAt)}
                </td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  {m.id === currentUserId && (
                    <span style={{ fontSize: '10px', color: '#3b82f6', fontFamily: 'IBM Plex Mono, monospace' }}>ty</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/* ─── Shared components ───────────────────────── */
function Card({ title, children, style }: { title: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={{ background: '#161922', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '8px', padding: '20px', ...style }}>
      <h3 style={{ fontSize: '13px', fontFamily: 'IBM Plex Mono, monospace', color: '#8b90a0', textTransform: 'uppercase', letterSpacing: '0.06em', margin: '0 0 16px' }}>
        {title}
      </h3>
      {children}
    </div>
  )
}

function FormField({ label, children, style }: { label: string; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div style={style}>
      <label style={{ display: 'block', fontSize: '12px', color: '#8b90a0', marginBottom: '5px', fontFamily: 'IBM Plex Mono, monospace' }}>
        {label}
      </label>
      {children}
    </div>
  )
}

function SaveButton({ loading, children, style }: { loading: boolean; children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <button
      type="submit"
      disabled={loading}
      style={{ padding: '8px 18px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 500, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1, ...style }}
    >
      {loading ? 'Zapisywanie...' : children}
    </button>
  )
}

function Alert({ msg, style }: { msg: { type: 'ok' | 'err'; text: string } | null; style?: React.CSSProperties }) {
  if (!msg) return null
  return (
    <div style={{
      padding: '10px 12px',
      borderRadius: '6px',
      fontSize: '12px',
      background: msg.type === 'ok' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
      border: `1px solid ${msg.type === 'ok' ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
      color: msg.type === 'ok' ? '#86efac' : '#fca5a5',
      marginTop: '8px',
      ...style,
    }}>
      {msg.text}
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <span style={{ fontSize: '12px', color: '#555b6e' }}>{label}</span>
      <span style={{ fontSize: '12px', color: '#8b90a0' }}>{children}</span>
    </div>
  )
}

function Mono({ children }: { children: React.ReactNode }) {
  return <span style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '11px' }}>{children}</span>
}

function InfoBadge({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '6px' }}>
      <div style={{ fontSize: '10px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</div>
      <div style={{ fontSize: '13px', color: '#e8eaf0', fontWeight: 500, marginTop: '2px' }}>{children}</div>
    </div>
  )
}

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    OWNER: { bg: 'rgba(245,158,11,0.15)', text: '#fcd34d', border: 'rgba(245,158,11,0.25)' },
    ABSI: { bg: 'rgba(59,130,246,0.15)', text: '#93c5fd', border: 'rgba(59,130,246,0.25)' },
    READONLY: { bg: 'rgba(255,255,255,0.06)', text: '#8b90a0', border: 'rgba(255,255,255,0.1)' },
  }
  const c = colors[role] || colors.READONLY
  return (
    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontFamily: 'IBM Plex Mono, monospace', background: c.bg, color: c.text, border: `1px solid ${c.border}` }}>
      {ROLE_LABELS[role] || role}
    </span>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  background: '#0f1117',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '6px',
  color: '#e8eaf0',
  fontSize: '13px',
  outline: 'none',
  boxSizing: 'border-box',
}
