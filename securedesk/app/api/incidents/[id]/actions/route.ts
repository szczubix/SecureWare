import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { z } from 'zod'
import { NextResponse } from 'next/server'

const schema = z.object({
  content: z.string().min(3).max(2000),
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

  const body = await req.json()
  const parsed = schema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const action = await prisma.incidentAction.create({
    data: {
      incidentId: id,
      content: parsed.data.content,
      authorId: userId,
      authorName: session.user?.name || session.user?.email || '',
    },
  })

  return NextResponse.json({ data: action }, { status: 201 })
}
