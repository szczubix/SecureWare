import { prisma } from '@/lib/prisma'
import { sendRiskReviewReminder } from '@/lib/email'
import { NextResponse } from 'next/server'

// Call every 24h from external scheduler:
// curl -H "Authorization: Bearer $CRON_SECRET" https://yourdomain/api/cron/risk-reviews

const DAY_MS = 24 * 60 * 60 * 1000

export async function GET(req: Request) {
  const secret = process.env.CRON_SECRET
  if (secret) {
    const auth = req.headers.get('authorization')
    if (auth !== `Bearer ${secret}`) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
  }

  const now = new Date()

  // Risks that are overdue for review and either:
  // - never had a reminder sent (reviewReminderSentAt IS NULL), OR
  // - reminder was sent before the current nextReviewAt (i.e. review date was updated, became overdue again)
  const risks = await prisma.risk.findMany({
    where: {
      deletedAt: null,
      status: { notIn: ['CLOSED', 'ACCEPTED'] },
      nextReviewAt: { lt: now },
      OR: [
        { reviewReminderSentAt: null },
        // Prisma can't do col < col directly, so we handle re-send logic in code
      ],
    },
    select: {
      id: true,
      riskNumber: true,
      title: true,
      riskScore: true,
      owner: true,
      nextReviewAt: true,
      reviewReminderSentAt: true,
      organizationId: true,
    },
  })

  // Filter: only send if no reminder yet, or reminder was sent before current nextReviewAt
  const due = risks.filter(r => {
    if (!r.reviewReminderSentAt) return true
    return r.reviewReminderSentAt < r.nextReviewAt!
  })

  if (due.length === 0) {
    return NextResponse.json({ ok: true, processed: 0, sent: 0, skipped: 0, details: { sent: [], skipped: [] } })
  }

  // Batch-load org users
  const orgIds = [...new Set(due.map(r => r.organizationId))]
  const users = await prisma.user.findMany({
    where: { organizationId: { in: orgIds }, role: { in: ['OWNER', 'ABSI'] } },
    select: { email: true, organizationId: true },
  })
  const orgEmailMap = new Map<string, string[]>()
  for (const u of users) {
    if (!u.email) continue
    const arr = orgEmailMap.get(u.organizationId) || []
    arr.push(u.email)
    orgEmailMap.set(u.organizationId, arr)
  }

  const sent: Array<{ riskId: string; riskNumber: string; to: string[] }> = []
  const skipped: string[] = []

  for (const risk of due) {
    const toEmails = orgEmailMap.get(risk.organizationId) || []
    if (toEmails.length === 0) {
      skipped.push(`${risk.riskNumber}: no recipients`)
      continue
    }

    const daysOverdue = Math.max(1, Math.floor((now.getTime() - risk.nextReviewAt!.getTime()) / DAY_MS))

    try {
      await sendRiskReviewReminder({
        to: toEmails,
        riskNumber: risk.riskNumber,
        riskId: risk.id,
        title: risk.title,
        riskScore: risk.riskScore,
        owner: risk.owner,
        daysOverdue,
      })

      await prisma.risk.update({
        where: { id: risk.id },
        data: { reviewReminderSentAt: now },
      })

      sent.push({ riskId: risk.id, riskNumber: risk.riskNumber, to: toEmails })
    } catch (err) {
      console.error(`[risk-review-cron] Failed for ${risk.riskNumber}:`, err)
      skipped.push(`${risk.riskNumber}: send failed`)
    }
  }

  return NextResponse.json({
    ok: true,
    processed: due.length,
    sent: sent.length,
    skipped: skipped.length,
    details: { sent, skipped },
  })
}
