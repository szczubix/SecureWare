'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    organizationName: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const res = await fetch('/api/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form),
    })

    if (res.ok) {
      router.push('/login?registered=1')
    } else {
      const data = await res.json()
      setError(
        typeof data.error === 'string'
          ? data.error
          : data.error?.formErrors?.[0] || 'Błąd rejestracji'
      )
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f1117',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '420px',
        background: '#161922',
        border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: '12px',
        padding: '40px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: '24px',
            fontWeight: 600,
            color: '#3b82f6',
            letterSpacing: '-0.02em',
            marginBottom: '8px',
          }}>
            SecureDesk
          </div>
          <div style={{
            fontFamily: 'IBM Plex Mono, monospace',
            fontSize: '11px',
            color: '#555b6e',
            textTransform: 'uppercase',
            letterSpacing: '0.1em',
          }}>
            Utwórz nowe konto
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <Field label="Imię i nazwisko">
              <input
                type="text"
                required
                minLength={2}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Jan Kowalski"
                style={inputStyle}
              />
            </Field>
            <Field label="Adres email">
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="jan@firma.pl"
                style={inputStyle}
              />
            </Field>
            <Field label="Hasło">
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="Min. 8 znaków"
                style={inputStyle}
              />
            </Field>
            <Field label="Nazwa organizacji">
              <input
                type="text"
                required
                minLength={2}
                value={form.organizationName}
                onChange={(e) => setForm({ ...form, organizationName: e.target.value })}
                placeholder="Firma Sp. z o.o."
                style={inputStyle}
              />
            </Field>
          </div>

          {error && (
            <div style={{
              marginTop: '14px',
              padding: '10px 14px',
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: '6px',
              color: '#fca5a5',
              fontSize: '13px',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              marginTop: '20px',
              padding: '11px',
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'Tworzenie konta...' : 'Zarejestruj się'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '13px', color: '#555b6e' }}>
          Masz już konto?{' '}
          <Link href="/login" style={{ color: '#3b82f6', textDecoration: 'none' }}>
            Zaloguj się
          </Link>
        </div>
      </div>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  background: '#0f1117',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '6px',
  color: '#e8eaf0',
  fontSize: '14px',
  outline: 'none',
  boxSizing: 'border-box',
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label style={{
        display: 'block',
        fontSize: '12px',
        color: '#8b90a0',
        marginBottom: '6px',
        fontFamily: 'IBM Plex Mono, monospace',
      }}>
        {label}
      </label>
      {children}
    </div>
  )
}
