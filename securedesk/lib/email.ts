import { Resend } from 'resend'

const resend = new Resend(process.env.RESEND_API_KEY)
const FROM = process.env.EMAIL_FROM || 'SecureDesk <noreply@securedesk.pl>'
const APP_URL = process.env.NEXTAUTH_URL || 'http://localhost:3000'

export interface Nis2ReminderParams {
  to: string[]
  incidentNumber: string
  incidentId: string
  title: string
  severity: string
  reminderType: '24h_warning' | '72h_report' | '30d_final' | 'overdue_24h' | 'overdue_72h' | 'overdue_30d'
  elapsedHours: number
  deadlineHours: number
}

const SEVERITY_PL: Record<string, string> = {
  CRITICAL: 'KRYTYCZNY',
  HIGH: 'WYSOKI',
  MEDIUM: 'ŚREDNI',
  LOW: 'NISKI',
}

const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH: '#f97316',
  MEDIUM: '#f59e0b',
  LOW: '#3b82f6',
}

function remainingTime(elapsedH: number, deadlineH: number): string {
  const remainH = deadlineH - elapsedH
  if (remainH <= 0) {
    const overdueH = Math.abs(remainH)
    if (overdueH >= 24) return `${Math.floor(overdueH / 24)} dni opóźnienia`
    return `${Math.round(overdueH)} godzin opóźnienia`
  }
  if (remainH >= 24) return `${Math.floor(remainH)} godz. (${Math.floor(remainH / 24)}d ${Math.floor(remainH % 24)}h)`
  return `${Math.floor(remainH)} godzin ${Math.floor((remainH % 1) * 60)} minut`
}

const REMINDER_META: Record<Nis2ReminderParams['reminderType'], { subject: string; step: string; deadlineLabel: string; color: string; overdue: boolean }> = {
  '24h_warning':  { subject: '⚠ NIS2: Zbliża się termin wczesnego ostrzeżenia (24h)',     step: 'Krok 1 — Wczesne ostrzeżenie',  deadlineLabel: '24 godziny od wykrycia',    color: '#f59e0b', overdue: false },
  '72h_report':   { subject: '⚠ NIS2: Zbliża się termin raportu do organu (72h)',          step: 'Krok 2 — Raport do organu nadzoru', deadlineLabel: '72 godziny od wykrycia', color: '#f97316', overdue: false },
  '30d_final':    { subject: '⚠ NIS2: Zbliża się termin raportu końcowego (30 dni)',        step: 'Krok 3 — Raport końcowy',        deadlineLabel: '30 dni od wykrycia',        color: '#f97316', overdue: false },
  'overdue_24h':  { subject: '🚨 NIS2 ALERT: Przekroczono termin wczesnego ostrzeżenia!',  step: 'Krok 1 — Wczesne ostrzeżenie',  deadlineLabel: '24 godziny od wykrycia',    color: '#ef4444', overdue: true  },
  'overdue_72h':  { subject: '🚨 NIS2 ALERT: Przekroczono termin raportu do organu!',      step: 'Krok 2 — Raport do organu nadzoru', deadlineLabel: '72 godziny od wykrycia', color: '#ef4444', overdue: true  },
  'overdue_30d':  { subject: '🚨 NIS2 ALERT: Przekroczono termin raportu końcowego!',      step: 'Krok 3 — Raport końcowy',        deadlineLabel: '30 dni od wykrycia',        color: '#ef4444', overdue: true  },
}

function buildHtml(p: Nis2ReminderParams): string {
  const meta = REMINDER_META[p.reminderType]
  const sevColor = SEVERITY_COLOR[p.severity] || '#8b90a0'
  const sevLabel = SEVERITY_PL[p.severity] || p.severity
  const incidentUrl = `${APP_URL}/incidents/${p.incidentId}`
  const remaining = remainingTime(p.elapsedHours, p.deadlineHours)
  const isOverdue = meta.overdue

  return `<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f1117;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:#161922;border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;">

    <!-- Header -->
    <div style="background:${isOverdue ? '#7f1d1d' : '#1e2433'};padding:24px 32px;border-bottom:3px solid ${meta.color};">
      <div style="font-family:'Courier New',monospace;font-size:13px;color:${meta.color};font-weight:600;letter-spacing:0.05em;margin-bottom:6px;">
        SECUREDESK · ALERT NIS2
      </div>
      <h1 style="margin:0;font-size:18px;color:#e8eaf0;font-weight:600;line-height:1.4;">
        ${isOverdue ? '🚨' : '⚠️'} ${meta.step}
        ${isOverdue ? '<span style="color:#ef4444;"> — TERMIN PRZEKROCZONY</span>' : ' — Zbliża się termin'}
      </h1>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">

      <!-- Incident card -->
      <div style="background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-left:3px solid ${sevColor};border-radius:8px;padding:16px 20px;margin-bottom:24px;">
        <div style="font-family:'Courier New',monospace;font-size:11px;color:#555b6e;margin-bottom:6px;">INCYDENT</div>
        <div style="font-family:'Courier New',monospace;font-size:13px;color:#3b82f6;margin-bottom:4px;">${p.incidentNumber}</div>
        <div style="font-size:15px;color:#e8eaf0;font-weight:600;margin-bottom:8px;">${p.title}</div>
        <span style="display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;font-family:'Courier New',monospace;background:rgba(${sevColor.slice(1).match(/.{2}/g)?.map(h => parseInt(h, 16)).join(',') || '59,130,246'},0.15);color:${sevColor};border:1px solid ${sevColor}40;">
          ${sevLabel}
        </span>
      </div>

      <!-- Timer info -->
      <div style="display:flex;gap:12px;margin-bottom:24px;">
        <div style="flex:1;background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:14px 16px;text-align:center;">
          <div style="font-size:11px;color:#555b6e;margin-bottom:4px;font-family:'Courier New',monospace;">TERMIN</div>
          <div style="font-size:13px;color:#e8eaf0;font-weight:600;">${meta.deadlineLabel}</div>
        </div>
        <div style="flex:1;background:${isOverdue ? 'rgba(239,68,68,0.1)' : 'rgba(245,158,11,0.1)'};border:1px solid ${isOverdue ? 'rgba(239,68,68,0.3)' : 'rgba(245,158,11,0.3)'};border-radius:8px;padding:14px 16px;text-align:center;">
          <div style="font-size:11px;color:#555b6e;margin-bottom:4px;font-family:'Courier New',monospace;">${isOverdue ? 'OPÓŹNIENIE' : 'POZOSTAŁO'}</div>
          <div style="font-size:14px;color:${isOverdue ? '#ef4444' : '#f59e0b'};font-weight:700;">${remaining}</div>
        </div>
      </div>

      <!-- NIS2 steps status -->
      <div style="background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:16px 20px;margin-bottom:24px;">
        <div style="font-family:'Courier New',monospace;font-size:11px;color:#555b6e;margin-bottom:12px;">PROCEDURA NIS2 — ART. 21</div>
        ${[
          { label: 'Wczesne ostrzeżenie',    deadline: '24h', active: p.reminderType.includes('24h') },
          { label: 'Raport do organu nadzoru', deadline: '72h', active: p.reminderType.includes('72h') },
          { label: 'Raport końcowy',           deadline: '30d', active: p.reminderType.includes('30d') },
        ].map((s, i) => `
        <div style="display:flex;align-items:center;gap:10px;padding:6px 0;${i < 2 ? 'border-bottom:1px solid rgba(255,255,255,0.05);' : ''}">
          <div style="width:20px;height:20px;border-radius:50%;background:${s.active ? meta.color + '30' : 'rgba(255,255,255,0.05)'};border:2px solid ${s.active ? meta.color : 'rgba(255,255,255,0.1)'};flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:10px;color:${s.active ? meta.color : '#555b6e'};">
            ${i + 1}
          </div>
          <div style="flex:1;font-size:13px;color:${s.active ? '#e8eaf0' : '#555b6e'};">${s.label}</div>
          <div style="font-family:'Courier New',monospace;font-size:11px;color:${s.active ? meta.color : '#3a3f52'};">${s.deadline}</div>
        </div>`).join('')}
      </div>

      <!-- CTA -->
      <div style="text-align:center;margin-bottom:8px;">
        <a href="${incidentUrl}" style="display:inline-block;padding:12px 28px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;">
          Otwórz incydent w SecureDesk →
        </a>
      </div>
    </div>

    <!-- Footer -->
    <div style="padding:16px 32px;border-top:1px solid rgba(255,255,255,0.05);text-align:center;">
      <p style="margin:0;font-size:11px;color:#3a3f52;font-family:'Courier New',monospace;">
        SecureDesk · Automatyczne powiadomienie NIS2 · Nie odpowiadaj na tę wiadomość
      </p>
    </div>
  </div>
</body>
</html>`
}

export interface RiskReviewReminderParams {
  to: string[]
  riskNumber: string
  riskId: string
  title: string
  riskScore: number
  owner: string
  daysOverdue: number
}

function riskScoreLabel(s: number) {
  if (s >= 15) return { label: 'Krytyczne', color: '#ef4444' }
  if (s >= 10) return { label: 'Wysokie',   color: '#f97316' }
  if (s >= 5)  return { label: 'Średnie',   color: '#f59e0b' }
  return             { label: 'Niskie',    color: '#22c55e' }
}

function buildRiskReviewHtml(p: RiskReviewReminderParams): string {
  const riskUrl = `${APP_URL}/risks/${p.riskId}`
  const lvl = riskScoreLabel(p.riskScore)
  const overdueText = p.daysOverdue === 1 ? '1 dzień' : `${p.daysOverdue} dni`

  return `<!DOCTYPE html>
<html lang="pl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0f1117;font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:600px;margin:32px auto;background:#161922;border:1px solid rgba(255,255,255,0.08);border-radius:12px;overflow:hidden;">

    <div style="background:#1e2433;padding:24px 32px;border-bottom:3px solid #f59e0b;">
      <div style="font-family:'Courier New',monospace;font-size:13px;color:#f59e0b;font-weight:600;letter-spacing:0.05em;margin-bottom:6px;">
        SECUREDESK · REJESTR RYZYK ISO 27001
      </div>
      <h1 style="margin:0;font-size:18px;color:#e8eaf0;font-weight:600;line-height:1.4;">
        ⚠️ Przegląd ryzyka jest przeterminowany
      </h1>
    </div>

    <div style="padding:28px 32px;">

      <div style="background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-left:3px solid ${lvl.color};border-radius:8px;padding:16px 20px;margin-bottom:24px;">
        <div style="font-family:'Courier New',monospace;font-size:11px;color:#555b6e;margin-bottom:6px;">RYZYKO</div>
        <div style="font-family:'Courier New',monospace;font-size:13px;color:#3b82f6;margin-bottom:4px;">${p.riskNumber}</div>
        <div style="font-size:15px;color:#e8eaf0;font-weight:600;margin-bottom:8px;">${p.title}</div>
        <span style="display:inline-block;padding:2px 10px;border-radius:4px;font-size:12px;font-family:'Courier New',monospace;font-weight:700;color:${lvl.color};background:${lvl.color}20;border:1px solid ${lvl.color}50;">
          ${p.riskScore} · ${lvl.label}
        </span>
      </div>

      <div style="display:flex;gap:12px;margin-bottom:24px;">
        <div style="flex:1;background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:14px 16px;text-align:center;">
          <div style="font-size:11px;color:#555b6e;margin-bottom:4px;font-family:'Courier New',monospace;">WŁAŚCICIEL RYZYKA</div>
          <div style="font-size:13px;color:#e8eaf0;font-weight:600;">${p.owner}</div>
        </div>
        <div style="flex:1;background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:8px;padding:14px 16px;text-align:center;">
          <div style="font-size:11px;color:#555b6e;margin-bottom:4px;font-family:'Courier New',monospace;">OPÓŹNIENIE PRZEGLĄDU</div>
          <div style="font-size:16px;color:#f59e0b;font-weight:700;">${overdueText}</div>
        </div>
      </div>

      <div style="background:#0f1117;border:1px solid rgba(255,255,255,0.07);border-radius:8px;padding:14px 20px;margin-bottom:24px;">
        <div style="font-size:13px;color:#8b90a0;line-height:1.6;">
          Zgodnie z wymaganiami ISO 27001:2022, ryzyka powinny być regularnie przeglądane.
          Proszę dokonać przeglądu ryzyka, zaktualizować ocenę i datę następnego przeglądu.
        </div>
      </div>

      <div style="text-align:center;">
        <a href="${riskUrl}" style="display:inline-block;padding:12px 28px;background:#3b82f6;color:#fff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;">
          Otwórz ryzyko w SecureDesk →
        </a>
      </div>
    </div>

    <div style="padding:16px 32px;border-top:1px solid rgba(255,255,255,0.05);text-align:center;">
      <p style="margin:0;font-size:11px;color:#3a3f52;font-family:'Courier New',monospace;">
        SecureDesk · Automatyczne przypomnienie ISO 27001 · Nie odpowiadaj na tę wiadomość
      </p>
    </div>
  </div>
</body>
</html>`
}

export async function sendRiskReviewReminder(params: RiskReviewReminderParams): Promise<void> {
  if (!process.env.RESEND_API_KEY || process.env.RESEND_API_KEY === 're_placeholder') {
    console.log('[email] RESEND_API_KEY not set, skipping risk review reminder')
    console.log(`[email] Would send to: ${params.to} | Risk: ${params.riskNumber} | Overdue: ${params.daysOverdue}d`)
    return
  }

  await resend.emails.send({
    from: FROM,
    to: params.to,
    subject: `[${params.riskNumber}] ⚠ Przegląd ryzyka przeterminowany o ${params.daysOverdue} ${params.daysOverdue === 1 ? 'dzień' : 'dni'}`,
    html: buildRiskReviewHtml(params),
  })
}

export async function sendNis2Reminder(params: Nis2ReminderParams): Promise<void> {
  if (!process.env.RESEND_API_KEY || process.env.RESEND_API_KEY === 're_placeholder') {
    console.log('[email] RESEND_API_KEY not set, skipping email send')
    console.log('[email] Would send to:', params.to, '| Subject:', REMINDER_META[params.reminderType].subject)
    return
  }

  const meta = REMINDER_META[params.reminderType]

  await resend.emails.send({
    from: FROM,
    to: params.to,
    subject: `[${params.incidentNumber}] ${meta.subject}`,
    html: buildHtml(params),
  })
}
