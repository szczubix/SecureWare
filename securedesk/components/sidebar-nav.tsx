'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut } from 'next-auth/react'

interface SidebarNavProps {
  openIncidents: number
  userName: string
  userRole: string
}

const ROLE_LABELS: Record<string, string> = {
  OWNER: 'Właściciel',
  ABSI: 'ABSI',
  READONLY: 'Tylko odczyt',
}

export function SidebarNav({ openIncidents, userName, userRole }: SidebarNavProps) {
  const pathname = usePathname()

  function isActive(href: string, exact = false) {
    return exact ? pathname === href : pathname.startsWith(href)
  }

  const linkStyle = (href: string, exact = false) => ({
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '7px 12px',
    borderRadius: '6px',
    fontSize: '13px',
    color: isActive(href, exact) ? '#e8eaf0' : '#8b90a0',
    background: isActive(href, exact) ? 'rgba(59,130,246,0.1)' : 'transparent',
    textDecoration: 'none',
    transition: 'all 0.15s',
    fontWeight: isActive(href, exact) ? 500 : 400,
  })

  return (
    <aside style={{
      width: '200px',
      minWidth: '200px',
      background: '#161922',
      borderRight: '1px solid rgba(255,255,255,0.07)',
      display: 'flex',
      flexDirection: 'column',
      padding: '16px 12px',
    }}>
      {/* Logo */}
      <div style={{ padding: '8px 12px 20px' }}>
        <div style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: '16px',
          fontWeight: 600,
          color: '#3b82f6',
          letterSpacing: '-0.02em',
        }}>
          SecureDesk
        </div>
        <div style={{
          fontFamily: 'IBM Plex Mono, monospace',
          fontSize: '10px',
          color: '#555b6e',
          marginTop: '2px',
        }}>
          v0.1
        </div>
      </div>

      {/* OPERACJE */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          fontSize: '10px',
          fontFamily: 'IBM Plex Mono, monospace',
          color: '#555b6e',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          padding: '0 12px',
          marginBottom: '6px',
        }}>
          Operacje
        </div>
        <Link href="/" style={linkStyle('/', true)}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
          </svg>
          Dashboard
        </Link>
        <Link href="/incidents" style={linkStyle('/incidents')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          </svg>
          Incydenty
          {openIncidents > 0 && (
            <span style={{
              marginLeft: 'auto',
              background: 'rgba(239,68,68,0.15)',
              color: '#fca5a5',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: '10px',
              fontSize: '10px',
              padding: '1px 6px',
              fontFamily: 'IBM Plex Mono, monospace',
            }}>
              {openIncidents}
            </span>
          )}
        </Link>
        <Link href="/assets" style={linkStyle('/assets')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
          </svg>
          Aktywa
        </Link>
        <Link href="/risks" style={linkStyle('/risks')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
          Ryzyka
        </Link>
      </div>

      {/* ZGODNOŚĆ (disabled) */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{
          fontSize: '10px',
          fontFamily: 'IBM Plex Mono, monospace',
          color: '#555b6e',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          padding: '0 12px',
          marginBottom: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          Zgodność
          <span style={{
            fontSize: '9px',
            background: 'rgba(59,130,246,0.1)',
            color: '#3b82f6',
            border: '1px solid rgba(59,130,246,0.2)',
            borderRadius: '4px',
            padding: '1px 4px',
            fontFamily: 'IBM Plex Mono, monospace',
          }}>v2</span>
        </div>
        {['Kontrolki ISO', 'Dokumenty', 'Uprawnienia'].map((label) => (
          <div key={label} style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            color: '#3a3f52',
            cursor: 'not-allowed',
          }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" opacity="0.4">
              <circle cx="12" cy="12" r="10"/>
            </svg>
            {label}
          </div>
        ))}
      </div>

      {/* KONTO */}
      <div style={{ marginTop: 'auto' }}>
        <div style={{
          fontSize: '10px',
          fontFamily: 'IBM Plex Mono, monospace',
          color: '#555b6e',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          padding: '0 12px',
          marginBottom: '6px',
        }}>
          Konto
        </div>
        <Link href="/settings" style={linkStyle('/settings')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
          Ustawienia
        </Link>
        <button
          onClick={() => signOut({ callbackUrl: '/login' })}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            borderRadius: '6px',
            fontSize: '13px',
            color: '#8b90a0',
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            width: '100%',
            textAlign: 'left',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          Wyloguj
        </button>

        {/* User info */}
        <div style={{
          marginTop: '16px',
          padding: '10px 12px',
          background: 'rgba(255,255,255,0.03)',
          borderRadius: '6px',
          borderTop: '1px solid rgba(255,255,255,0.05)',
        }}>
          <div style={{ fontSize: '12px', color: '#e8eaf0', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {userName}
          </div>
          <div style={{ fontSize: '11px', color: '#555b6e', fontFamily: 'IBM Plex Mono, monospace', marginTop: '2px' }}>
            {ROLE_LABELS[userRole] || userRole}
          </div>
        </div>
      </div>
    </aside>
  )
}
