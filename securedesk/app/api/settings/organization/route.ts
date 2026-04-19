import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const schema = z.object({
  name: z.string().min(2).max(200),
})

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const org = await prisma.organization.findUnique({
    where: { id: orgId },
    select: {
      id: true,
      name: true,
      plan: true,
      createdAt: true,
      _count: { select: { users: true, incidents: true, assets: true } },
    },
  })

  return NextResponse.json({ data: org })
}

export async function PATCH(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!
  const role = (session.user as { role?: string }).role

  if (role !== 'OWNER') {
    return NextResponse.json({ error: 'Brak uprawnień — wymagana rola OWNER' }, { status: 403 })
  }

  const body = await req.json()
  const parsed = schema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const org = await prisma.organization.update({
    where: { id: orgId },
    data: { name: parsed.data.name },
    select: { id: true, name: true, plan: true },
  })

  return NextResponse.json({ data: org })
}
