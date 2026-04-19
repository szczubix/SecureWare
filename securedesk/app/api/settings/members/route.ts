import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import { NextResponse } from 'next/server'

const inviteSchema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
  role: z.enum(['OWNER', 'ABSI', 'READONLY']),
  password: z.string().min(8),
})

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const members = await prisma.user.findMany({
    where: { organizationId: orgId },
    select: { id: true, email: true, name: true, role: true, createdAt: true },
    orderBy: { createdAt: 'asc' },
  })

  return NextResponse.json({ data: members })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!
  const role = (session.user as { role?: string }).role

  if (role !== 'OWNER') {
    return NextResponse.json({ error: 'Brak uprawnień — wymagana rola OWNER' }, { status: 403 })
  }

  const body = await req.json()
  const parsed = inviteSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const existing = await prisma.user.findUnique({ where: { email: parsed.data.email } })
  if (existing) {
    return NextResponse.json({ error: 'Użytkownik z tym adresem email już istnieje' }, { status: 409 })
  }

  const hashed = await bcrypt.hash(parsed.data.password, 12)
  const user = await prisma.user.create({
    data: {
      email: parsed.data.email,
      name: parsed.data.name,
      role: parsed.data.role,
      password: hashed,
      organizationId: orgId,
    },
    select: { id: true, email: true, name: true, role: true, createdAt: true },
  })

  return NextResponse.json({ data: user }, { status: 201 })
}
