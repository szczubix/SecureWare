import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const schema = z.object({
  action: z.enum(['early_warning', 'report_72h', 'final_report']),
})

export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!
  const userId = (session.user as { id?: string }).id!

  const { id } = await params

  const incident = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!incident) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })
  if (!incident.nis2Active) return NextResponse.json({ error: 'Incydent nie jest oznaczony jako NIS2' }, { status: 400 })

  const body = await req.json()
  const parsed = schema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const now = new Date()
  const updateData: Record<string, unknown> = {}
  let actionContent = ''

  if (parsed.data.action === 'early_warning') {
    if (incident.nis2EarlyWarningSentAt) {
      return NextResponse.json({ error: 'Early warning został już wysłany' }, { status: 409 })
    }
    updateData.nis2EarlyWarningSentAt = now
    actionContent = '📤 NIS2 Early Warning (24h) — raport wstępny wysłany do właściwego organu nadzoru (CERT Polska / UKNF).'
  } else if (parsed.data.action === 'report_72h') {
    if (incident.nis2ReportSentAt) {
      return NextResponse.json({ error: 'Raport 72h został już wysłany' }, { status: 409 })
    }
    updateData.nis2ReportSentAt = now
    actionContent = '📋 NIS2 Raport 72h — szczegółowe zgłoszenie incydentu wysłane do organu nadzoru zgodnie z Art. 21 dyrektywy NIS2.'
  } else {
    actionContent = '✅ NIS2 Raport końcowy — pełna dokumentacja incydentu przekazana do organu nadzoru. Procedura NIS2 zakończona.'
  }

  await prisma.incident.update({ where: { id }, data: updateData })

  await prisma.incidentAction.create({
    data: {
      incidentId: id,
      content: actionContent,
      authorId: userId,
      authorName: session.user?.name || session.user?.email || '',
    },
  })

  return NextResponse.json({ success: true, timestamp: now })
}
