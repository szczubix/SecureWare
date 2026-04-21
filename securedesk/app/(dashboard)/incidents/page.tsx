import { Suspense } from 'react'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { IncidentsList } from '@/components/incidents-list'

export default async function IncidentsPage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  const currentUserName = session.user?.name || session.user?.email || ''

  return (
    <Suspense fallback={<div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>}>
      <IncidentsList currentUserName={currentUserName} />
    </Suspense>
  )
}
