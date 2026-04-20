import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

const TYPE_PL: Record<string, string> = { HARDWARE: 'Sprzęt', SOFTWARE: 'Oprogramowanie', DATA: 'Dane', CLOUD_SERVICE: 'Usługa cloud', INFRASTRUCTURE: 'Infrastruktura', OTHER: 'Inne' }
const CLASS_PL: Record<string, string> = { RESTRICTED: 'Zastrzeżony', CONFIDENTIAL: 'Poufny', INTERNAL: 'Wewnętrzny', PUBLIC: 'Publiczny' }

function csvCell(val: string | number | null | undefined): string {
  const s = String(val ?? '')
  if (s.includes('"') || s.includes(',') || s.includes('\n') || s.includes('\r')) {
    return `"${s.replace(/"/g, '""')}"`
  }
  return s
}

function fmtDate(d: Date | string | null | undefined): string {
  if (!d) return ''
  return new Date(d).toLocaleString('pl-PL', { timeZone: 'Europe/Warsaw' })
}

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const { searchParams } = new URL(req.url)
  const type = searchParams.get('type')
  const classification = searchParams.get('classification')
  const noOwner = searchParams.get('noOwner')
  const overdueReview = searchParams.get('overdueReview')
  const search = searchParams.get('search')

  const assets = await prisma.asset.findMany({
    where: {
      organizationId: orgId,
      deletedAt: null,
      ...(type && { type: type as never }),
      ...(classification && { classification: classification as never }),
      ...(noOwner === 'true' && { businessOwner: null, technicalOwner: null }),
      ...(overdueReview === 'true' && { nextReviewAt: { lt: new Date() } }),
      ...(search && {
        OR: [
          { name: { contains: search, mode: 'insensitive' as const } },
          { assetNumber: { contains: search, mode: 'insensitive' as const } },
          { location: { contains: search, mode: 'insensitive' as const } },
          { businessOwner: { contains: search, mode: 'insensitive' as const } },
          { technicalOwner: { contains: search, mode: 'insensitive' as const } },
        ],
      }),
    },
    include: { _count: { select: { incidents: true } } },
    orderBy: { createdAt: 'desc' },
    take: 10000,
  })

  const headers = [
    'Nr aktywa', 'Nazwa', 'Typ', 'Klasyfikacja', 'Lokalizacja',
    'Właściciel biznesowy', 'Właściciel techniczny',
    'Powiązane incydenty', 'Termin przeglądu', 'Data dodania', 'Opis',
  ]

  const now = new Date()
  const rows = assets.map(a => [
    a.assetNumber,
    a.name,
    TYPE_PL[a.type] || a.type,
    CLASS_PL[a.classification] || a.classification,
    a.location || '',
    a.businessOwner || '',
    a.technicalOwner || '',
    a._count.incidents,
    a.nextReviewAt ? fmtDate(a.nextReviewAt) + (a.nextReviewAt < now ? ' (PRZETERMINOWANY)' : '') : '',
    fmtDate(a.createdAt),
    a.description || '',
  ].map(csvCell).join(','))

  const csv = '\uFEFF' + [headers.map(csvCell).join(','), ...rows].join('\r\n')
  const filename = `aktywa_${new Date().toISOString().slice(0, 10)}.csv`

  return new Response(csv, {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="${filename}"`,
    },
  })
}
