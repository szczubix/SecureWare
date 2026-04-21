import { Suspense } from 'react'
import { ControlsList } from '@/components/controls-list'

export default function ControlsPage() {
  return (
    <Suspense fallback={<div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>}>
      <ControlsList />
    </Suspense>
  )
}
