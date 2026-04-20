import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

const SEVERITY_PL: Record<string, string> = { CRITICAL: 'Krytyczny', HIGH: 'Wysoki', MEDIUM: 'Średni', LOW: 'Niski', INFO: 'Informacja' }
const STATUS_PL: Record<string, string> = { NEW: 'Nowy', IN_PROGRESS: 'W toku', ANALYSIS: 'Analiza', CLOSED: 'Zamknięty' }
const CATEGORY_PL: Record<string, string> = { UNAUTHORIZED_ACCESS: 'Nieautoryzowany dostęp', DATA_LEAK: 'Wyciek danych', AVAILABILITY: 'Niedostępność', PHISHING: 'Phishing', MALWARE: 'Złośliwe oprogramowanie', PHYSICAL: 'Incydent fizyczny', OTHER: 'Inne' }

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
  const status = searchParams.get('status')
  const severity = searchParams.get('severity')
  const category = searchParams.get('category')
  const nis2 = searchParams.get('nis2')
  const search = searchParams.get('search')
  const dateFrom = searchParams.get('dateFrom')
  const dateTo = searchParams.get('dateTo')

  const incidents = await prisma.incident.findMany({
    where: {
      organizationId: orgId,
      deletedAt: null,
      ...(status && { status: status as never }),
      ...(severity && { severity: severity as never }),
      ...(category && { category: category as never }),
      ...(nis2 === 'true' && { nis2Active: true }),
      ...(dateFrom || dateTo ? {
        createdAt: {
          ...(dateFrom && { gte: new Date(dateFrom) }),
          ...(dateTo && { lte: new Date(dateTo + 'T23:59:59Z') }),
        },
      } : {}),
      ...(search && {
        OR: [
          { title: { contains: search, mode: 'insensitive' as const } },
          { incidentNumber: { contains: search, mode: 'insensitive' as const } },
          { reportedBy: { contains: search, mode: 'insensitive' as const } },
        ],
      }),
    },
    include: { _count: { select: { evidences: true, actions: true } } },
    orderBy: { createdAt: 'desc' },
    take: 10000,
  })

  const headers = [
    'Nr incydentu', 'Tytuł', 'Ważność', 'Status', 'Kategoria',
    'Zgłaszający', 'Przypisany do', 'NIS2', 'Dowody', 'Akcje',
    'Data zgłoszenia', 'Data zamknięcia', 'Opis',
  ]

  const rows = incidents.map(inc => [
    inc.incidentNumber,
    inc.title,
    SEVERITY_PL[inc.severity] || inc.severity,
    STATUS_PL[inc.status] || inc.status,
    CATEGORY_PL[inc.category] || inc.category,
    inc.reportedBy,
    inc.assignedTo || '',
    inc.nis2Active ? 'Tak' : 'Nie',
    inc._count.evidences,
    inc._count.actions,
    fmtDate(inc.createdAt),
    fmtDate(inc.closedAt),
    inc.description,
  ].map(csvCell).join(','))

  // UTF-8 BOM for Excel compatibility with Polish characters
  const csv = '\uFEFF' + [headers.map(csvCell).join(','), ...rows].join('\r\n')
  const filename = `incydenty_${new Date().toISOString().slice(0, 10)}.csv`

  return new Response(csv, {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="${filename}"`,
    },
  })
}
