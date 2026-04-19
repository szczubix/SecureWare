import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { redirect, notFound } from 'next/navigation'
import { IncidentDetail } from '@/components/incident-detail'

export default async function IncidentPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const { id } = await params
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const incident = await prisma.incident.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      actions: { orderBy: { createdAt: 'asc' } },
      evidences: true,
      assets: { include: { asset: true } },
    },
  })

  if (!incident) notFound()

  return (
    <IncidentDetail
      incident={JSON.parse(JSON.stringify(incident))}
      currentUser={{
        id: (session.user as { id?: string }).id || '',
        name: session.user?.name || session.user?.email || '',
      }}
    />
  )
}
