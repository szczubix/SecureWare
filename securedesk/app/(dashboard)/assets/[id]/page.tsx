import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { redirect, notFound } from 'next/navigation'
import { AssetDetail } from '@/components/asset-detail'

export default async function AssetPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const { id } = await params
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const asset = await prisma.asset.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      history: { orderBy: { createdAt: 'desc' }, take: 20 },
      incidents: {
        include: {
          incident: {
            select: {
              id: true, incidentNumber: true, title: true,
              severity: true, status: true, createdAt: true,
            },
          },
        },
      },
    },
  })

  if (!asset) notFound()

  return (
    <AssetDetail
      asset={JSON.parse(JSON.stringify(asset))}
      currentUser={{ name: session.user?.name || session.user?.email || '' }}
    />
  )
}
