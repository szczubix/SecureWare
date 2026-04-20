import { Suspense } from 'react'
import { AssetsList } from '@/components/assets-list'

export default function AssetsPage() {
  return (
    <Suspense fallback={<div style={{ padding: '24px', color: '#555b6e' }}>Ładowanie...</div>}>
      <AssetsList />
    </Suspense>
  )
}
