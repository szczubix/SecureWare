import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const updateSchema = z.object({
  status: z.enum(['NEW', 'IN_PROGRESS', 'ANALYSIS', 'CLOSED']).optional(),
  severity: z.enum(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']).optional(),
  assignedTo: z.string().optional(),
  nis2Active: z.boolean().optional(),
  nis2EarlyWarningSentAt: z.string().datetime().optional().nullable(),
  nis2ReportSentAt: z.string().datetime().optional().nullable(),
  closureRootCause: z.string().optional(),
  closureActions: z.string().optional(),
  closurePreventive: z.string().optional(),
})

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params

  const incident = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      actions: { orderBy: { createdAt: 'asc' } },
      evidences: true,
      assets: { include: { asset: true } },
    },
  })

  if (!incident) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })
  return NextResponse.json({ data: incident })
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!
  const userId = (session.user as { id?: string }).id!

  const { id } = await params

  const existing = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  const body = await req.json()
  const parsed = updateSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const updateData: Record<string, unknown> = { ...parsed.data }

  if (parsed.data.status === 'CLOSED' && existing.status !== 'CLOSED') {
    updateData.closedAt = new Date()
  }
  if (parsed.data.nis2Active === true && !existing.nis2Active) {
    updateData.nis2StartedAt = new Date()
  }

  const incident = await prisma.incident.update({
    where: { id },
    data: updateData,
  })

  if (parsed.data.status && parsed.data.status !== existing.status) {
    const STATUS_LABELS: Record<string, string> = {
      NEW: 'Nowy', IN_PROGRESS: 'W toku', ANALYSIS: 'Analiza', CLOSED: 'Zamknięty',
    }
    await prisma.incidentAction.create({
      data: {
        incidentId: id,
        content: `Status zmieniony z "${STATUS_LABELS[existing.status]}" na "${STATUS_LABELS[parsed.data.status]}".`,
        authorId: userId,
        authorName: session.user?.name || session.user?.email || '',
      },
    })
  }

  return NextResponse.json({ data: incident })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params

  const existing = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!existing) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  await prisma.incident.update({
    where: { id },
    data: { deletedAt: new Date() },
  })

  return NextResponse.json({ success: true })
}
