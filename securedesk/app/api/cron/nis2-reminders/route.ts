import { prisma } from '@/lib/prisma'
import { sendNis2Reminder } from '@/lib/email'
import { NextResponse } from 'next/server'

// Call this endpoint from an external scheduler every 30 minutes
// e.g. cURL: curl -H "Authorization: Bearer $CRON_SECRET" https://yourdomain/api/cron/nis2-reminders

const HOUR_MS = 60 * 60 * 1000
const DAY_MS = 24 * HOUR_MS

// Reminder windows — send reminder when elapsed crosses these thresholds (hours)
const THRESHOLDS = {
  warn_24h:  { hours: 20,    type: '24h_warning'  as const, deadlineHours: 24  },
  over_24h:  { hours: 24,    type: 'overdue_24h'  as const, deadlineHours: 24  },
  warn_72h:  { hours: 68,    type: '72h_report'   as const, deadlineHours: 72  },
  over_72h:  { hours: 72,    type: 'overdue_72h'  as const, deadlineHours: 72  },
  warn_30d:  { hours: 696,   type: '30d_final'    as const, deadlineHours: 720 },  // 29 days
  over_30d:  { hours: 720,   type: 'overdue_30d'  as const, deadlineHours: 720 },  // 30 days
}

export async function GET(req: Request) {
  // Auth check
  const secret = process.env.CRON_SECRET
  if (secret) {
    const auth = req.headers.get('authorization')
    if (auth !== `Bearer ${secret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }

  const now = Date.now()
  const sent: Array<{ incidentId: string; type: string; to: string[] }> = []
  const skipped: string[] = []

  // Fetch all active NIS2 incidents with their org users
  const incidents = await prisma.incident.findMany({
    where: { nis2Active: true, deletedAt: null, nis2StartedAt: { not: null } },
    select: {
      id: true,
      incidentNumber: true,
      title: true,
      severity: true,
      nis2StartedAt: true,
      nis2EarlyWarningSentAt: true,
      nis2ReportSentAt: true,
      reminder24hSentAt: true,
      reminder72hSentAt: true,
      reminder30dSentAt: true,
      organizationId: true,
    },
  })

  // Batch-load org users
  const orgIds = [...new Set(incidents.map(i => i.organizationId))]
  const users = await prisma.user.findMany({
    where: {
      organizationId: { in: orgIds },
      role: { in: ['OWNER', 'ABSI'] },
    },
    select: { email: true, organizationId: true },
  })
  const orgEmailMap = new Map<string, string[]>()
  for (const u of users) {
    if (!u.email) continue
    const arr = orgEmailMap.get(u.organizationId) || []
    arr.push(u.email)
    orgEmailMap.set(u.organizationId, arr)
  }

  for (const inc of incidents) {
    const startedAt = inc.nis2StartedAt!
    const elapsedMs = now - startedAt.getTime()
    const elapsedH = elapsedMs / HOUR_MS
    const toEmails = orgEmailMap.get(inc.organizationId) || []

    if (toEmails.length === 0) {
      skipped.push(`${inc.incidentNumber}: no recipients`)
      continue
    }

    const step1Done = !!inc.nis2EarlyWarningSentAt
    const step2Done = !!inc.nis2ReportSentAt

    const updates: Partial<{
      reminder24hSentAt: Date
      reminder72hSentAt: Date
      reminder30dSentAt: Date
    }> = {}

    // Determine which reminder to send (process in priority order: overdue first)
    let reminderToSend: typeof THRESHOLDS[keyof typeof THRESHOLDS] | null = null
    let reminderField: 'reminder24hSentAt' | 'reminder72hSentAt' | 'reminder30dSentAt' | null = null

    if (!step1Done) {
      // Step 1 not done yet
      if (elapsedH >= THRESHOLDS.over_24h.hours && !inc.reminder24hSentAt) {
        reminderToSend = THRESHOLDS.over_24h
        reminderField = 'reminder24hSentAt'
      } else if (elapsedH >= THRESHOLDS.warn_24h.hours && !inc.reminder24hSentAt) {
        reminderToSend = THRESHOLDS.warn_24h
        reminderField = 'reminder24hSentAt'
      }
    } else if (!step2Done) {
      // Step 1 done, step 2 not done
      if (elapsedH >= THRESHOLDS.over_72h.hours && !inc.reminder72hSentAt) {
        reminderToSend = THRESHOLDS.over_72h
        reminderField = 'reminder72hSentAt'
      } else if (elapsedH >= THRESHOLDS.warn_72h.hours && !inc.reminder72hSentAt) {
        reminderToSend = THRESHOLDS.warn_72h
        reminderField = 'reminder72hSentAt'
      }
    } else {
      // Both done, check step 3 (30d final report)
      if (elapsedH >= THRESHOLDS.over_30d.hours && !inc.reminder30dSentAt) {
        reminderToSend = THRESHOLDS.over_30d
        reminderField = 'reminder30dSentAt'
      } else if (elapsedH >= THRESHOLDS.warn_30d.hours && !inc.reminder30dSentAt) {
        reminderToSend = THRESHOLDS.warn_30d
        reminderField = 'reminder30dSentAt'
      }
    }

    if (!reminderToSend || !reminderField) {
      skipped.push(`${inc.incidentNumber}: no reminder due (elapsed ${elapsedH.toFixed(1)}h)`)
      continue
    }

    try {
      await sendNis2Reminder({
        to: toEmails,
        incidentNumber: inc.incidentNumber,
        incidentId: inc.id,
        title: inc.title,
        severity: inc.severity,
        reminderType: reminderToSend.type,
        elapsedHours: elapsedH,
        deadlineHours: reminderToSend.deadlineHours,
      })

      updates[reminderField] = new Date()
      await prisma.incident.update({
        where: { id: inc.id },
        data: updates,
      })

      sent.push({ incidentId: inc.id, type: reminderToSend.type, to: toEmails })
    } catch (err) {
      console.error(`[nis2-cron] Failed to send for ${inc.incidentNumber}:`, err)
      skipped.push(`${inc.incidentNumber}: send failed`)
    }
  }

  return NextResponse.json({
    ok: true,
    processed: incidents.length,
    sent: sent.length,
    skipped: skipped.length,
    details: { sent, skipped },
  })
}
