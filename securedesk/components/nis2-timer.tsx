'use client'

import { useEffect, useState } from 'react'

interface NIS2TimerProps {
  startedAt: Date | string
  earlyWarningSentAt?: Date | string | null
  reportSentAt?: Date | string | null
}

export function NIS2Timer({ startedAt, earlyWarningSentAt, reportSentAt }: NIS2TimerProps) {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(interval)
  }, [])

  const start = new Date(startedAt).getTime()
  const elapsed = now.getTime() - start

  const deadline24h = 24 * 60 * 60 * 1000
  const deadline72h = 72 * 60 * 60 * 1000
  const deadline30d = 30 * 24 * 60 * 60 * 1000

  function formatRemaining(deadline: number): string {
    const remaining = deadline - elapsed
    if (remaining <= 0) {
      const over = Math.abs(remaining)
      const h = Math.floor(over / 3_600_000)
      return `przekroczony o ${h}h`
    }
    const h = Math.floor(remaining / 3_600_000)
    const m = Math.floor((remaining % 3_600_000) / 60_000)
    return `${h}h ${m}min`
  }

  const step1done = !!earlyWarningSentAt || elapsed > deadline24h
  const step2done = !!reportSentAt || elapsed > deadline72h
  const step2active = step1done && !step2done
  const step3active = step2done && elapsed < deadline30d

  const steps = [
    {
      label: 'Early warning 24h',
      done: step1done,
      active: !step1done && elapsed < deadline24h,
      time: step1done && earlyWarningSentAt ? '✓ wysłany' : formatRemaining(deadline24h),
    },
    {
      label: 'Raport 72h',
      done: step2done,
      active: step2active,
      time: step2done ? '✓ wysłany' : formatRemaining(deadline72h),
    },
    {
      label: 'Raport końcowy',
      done: elapsed > deadline30d,
      active: step3active,
      time: formatRemaining(deadline30d),
    },
  ]

  return (
    <div style={{
      background: '#161922',
      border: '1px solid rgba(245,158,11,0.2)',
      borderRadius: 8,
      padding: '14px 16px',
      marginBottom: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 10, color: '#f59e0b', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
          ● NIS2 Art. 21 — procedura raportowania
        </span>
        {step2active && (
          <span style={{ fontFamily: 'IBM Plex Mono', fontSize: 10, color: '#f59e0b' }}>
            pozostało {formatRemaining(deadline72h)} do raportu 72h
          </span>
        )}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 0 }}>
        {steps.map((step, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <div style={{
              width: 22,
              height: 22,
              borderRadius: '50%',
              background: step.done ? 'rgba(34,197,94,0.15)' : step.active ? 'rgba(245,158,11,0.15)' : 'rgba(255,255,255,0.05)',
              border: `2px solid ${step.done ? '#22c55e' : step.active ? '#f59e0b' : 'rgba(255,255,255,0.13)'}`,
              color: step.done ? '#22c55e' : step.active ? '#f59e0b' : '#555b6e',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 9, fontFamily: 'IBM Plex Mono', marginBottom: 6,
            }}>
              {step.done ? '✓' : i + 1}
            </div>
            <div style={{ fontFamily: 'IBM Plex Mono', fontSize: 9, textTransform: 'uppercase', color: step.done ? '#22c55e' : step.active ? '#f59e0b' : '#555b6e' }}>
              {step.label}
            </div>
            <div style={{ fontSize: 10, color: step.active ? '#f59e0b' : '#555b6e', marginTop: 2 }}>
              {step.time}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
