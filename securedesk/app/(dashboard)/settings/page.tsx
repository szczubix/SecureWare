import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { redirect } from 'next/navigation'
import { SettingsView } from '@/components/settings-view'

export default async function SettingsPage() {
  const session = await getServerSession(authOptions)
  if (!session) redirect('/login')

  return (
    <SettingsView
      user={{
        id: (session.user as { id?: string }).id || '',
        email: session.user?.email || '',
        name: session.user?.name || '',
        role: (session.user as { role?: string }).role || 'ABSI',
      }}
    />
  )
}
