import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { prisma } from '@/lib/prisma'
import { redirect, notFound } from 'next/navigation'
import { RiskDetail } from '@/components/risk-detail'

export default async function RiskPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const { id } = await params
  const orgId = (session.user as { organizationId?: string }).organizationId!

  const risk = await prisma.risk.findFirst({
    where: { id, organizationId: orgId, deletedAt: null },
    include: {
      assets: { include: { asset: { select: { id: true, assetNumber: true, name: true, type: true } } } },
    },
  })

  if (!risk) notFound()

  return (
    <RiskDetail
      risk={JSON.parse(JSON.stringify(risk))}
      currentUser={{ name: session.user?.name || session.user?.email || '' }}
    />
  )
}
