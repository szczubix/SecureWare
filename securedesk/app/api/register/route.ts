import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import bcrypt from 'bcryptjs'
import { NextResponse } from 'next/server'

const schema = z.object({
  name: z.string().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(8, 'Hasło musi mieć co najmniej 8 znaków'),
  organizationName: z.string().min(2).max(200),
})

export async function POST(req: Request) {
  const body = await req.json()
  const parsed = schema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const existing = await prisma.user.findUnique({ where: { email: parsed.data.email } })
  if (existing) {
    return NextResponse.json({ error: 'Konto z tym adresem email już istnieje' }, { status: 409 })
  }

  const hashed = await bcrypt.hash(parsed.data.password, 12)

  const org = await prisma.organization.create({
    data: { name: parsed.data.organizationName, plan: 'STARTER' },
  })

  await prisma.user.create({
    data: {
      email: parsed.data.email,
      name: parsed.data.name,
      password: hashed,
      role: 'OWNER',
      organizationId: org.id,
    },
  })

  return NextResponse.json({ success: true }, { status: 201 })
}
