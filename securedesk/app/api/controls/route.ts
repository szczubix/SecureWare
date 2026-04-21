import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'
import { ISO_CONTROLS } from '@/lib/iso-controls'

const patchSchema = z.object({
  controlNumber: z.string(),
  status: z.enum(['NOT_REVIEWED', 'APPLICABLE', 'PLANNED', 'EXCLUDED', 'NOT_APPLICABLE']).optional(),
  justification: z.string().optional().nullable(),
  owner: z.string().optional().nullable(),
})

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const saved = await prisma.isoControl.findMany({
    where: { organizationId: orgId },
  })

  const savedMap = new Map(saved.map(c => [c.controlNumber, c]))

  const controls = ISO_CONTROLS.map(def => {
    const db = savedMap.get(def.number)
    return {
      number: def.number,
      theme: def.theme,
      title: def.title,
      status: db?.status ?? 'NOT_REVIEWED',
      justification: db?.justification ?? null,
      owner: db?.owner ?? null,
      updatedAt: db?.updatedAt ?? null,
    }
  })

  const stats = {
    total: controls.length,
    applicable: controls.filter(c => c.status === 'APPLICABLE').length,
    planned: controls.filter(c => c.status === 'PLANNED').length,
    excluded: controls.filter(c => c.status === 'EXCLUDED').length,
    notApplicable: controls.filter(c => c.status === 'NOT_APPLICABLE').length,
    notReviewed: controls.filter(c => c.status === 'NOT_REVIEWED').length,
  }

  return NextResponse.json({ data: controls, stats })
}

export async function PATCH(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const body = await req.json()
  const parsed = patchSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const { controlNumber, ...data } = parsed.data

  const valid = ISO_CONTROLS.find(c => c.number === controlNumber)
  if (!valid) return NextResponse.json({ error: 'Nieznana kontrolka' }, { status: 400 })

  const control = await prisma.isoControl.upsert({
    where: { organizationId_controlNumber: { organizationId: orgId, controlNumber } },
    update: data,
    create: { organizationId: orgId, controlNumber, ...data },
  })

  return NextResponse.json({ data: control })
}
