import { Suspense } from 'react'
import { IncidentsList } from '@/components/incidents-list'

export default function IncidentsPage() {
  return (
    <Suspense fallback={<div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>}>
      <IncidentsList />
    </Suspense>
  )
}
