import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { ensureBucket, getPresignedUploadUrl, getPresignedDownloadUrl } from '@/lib/minio'
import { z } from 'zod'
import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'

const uploadSchema = z.object({
  filename: z.string().min(1).max(255),
  size: z.number().int().positive().max(50 * 1024 * 1024),
  mimeType: z.string().min(1),
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
  })
  if (!incident) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  const evidences = await prisma.evidence.findMany({
    where: { incidentId: id },
    orderBy: { createdAt: 'desc' },
  })

  // Generate download URLs for all evidences
  const withUrls = await Promise.all(
    evidences.map(async (ev) => {
      try {
        const url = await getPresignedDownloadUrl(ev.storagePath)
        return { ...ev, downloadUrl: url }
      } catch {
        return { ...ev, downloadUrl: null }
      }
    })
  )

  return NextResponse.json({ data: withUrls })
}

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
  const parsed = uploadSchema.safeParse(body)
  if (!parsed.success) return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })

  const ext = parsed.data.filename.split('.').pop() || 'bin'
  const storagePath = `evidences/${orgId}/${id}/${randomUUID()}.${ext}`

  try {
    await ensureBucket()
    const uploadUrl = await getPresignedUploadUrl(storagePath)

    // Create evidence record (will be "pending" until upload confirmed)
    const evidence = await prisma.evidence.create({
      data: {
        filename: parsed.data.filename,
        storagePath,
        size: parsed.data.size,
        mimeType: parsed.data.mimeType,
        incidentId: id,
        uploadedBy: session.user?.name || session.user?.email || userId,
      },
    })

    return NextResponse.json({ data: { evidence, uploadUrl } }, { status: 201 })
  } catch {
    return NextResponse.json({ error: 'Błąd połączenia z magazynem plików (MinIO)' }, { status: 503 })
  }
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { id } = await params
  const { searchParams } = new URL(req.url)
  const evidenceId = searchParams.get('evidenceId')
  if (!evidenceId) return NextResponse.json({ error: 'Brak evidenceId' }, { status: 400 })

  const incident = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
  })
  if (!incident) return NextResponse.json({ error: 'Nie znaleziono' }, { status: 404 })

  await prisma.evidence.delete({ where: { id: evidenceId } })
  return NextResponse.json({ success: true })
}
