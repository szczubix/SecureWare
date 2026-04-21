import { Suspense } from 'react'
import { RisksList } from '@/components/risks-list'

export default function RisksPage() {
  return (
    <Suspense fallback={<div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>}>
      <RisksList />
    </Suspense>
  )
}
