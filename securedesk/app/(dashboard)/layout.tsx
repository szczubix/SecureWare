import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { SidebarNav } from '@/components/sidebar-nav'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const orgId = (session.user as { organizationId?: string }).organizationId!
  const openIncidents = await prisma.incident.count({
    where: {
      organizationId: orgId,
      status: { in: ['NEW', 'IN_PROGRESS', 'ANALYSIS'] },
      deletedAt: null,
    },
  })

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#0f1117' }}>
      <SidebarNav
        openIncidents={openIncidents}
        userName={session.user?.name || session.user?.email || ''}
        userRole={(session.user as { role?: string }).role || 'ABSI'}
      />
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
        {children}
      </main>
    </div>
  )
}
