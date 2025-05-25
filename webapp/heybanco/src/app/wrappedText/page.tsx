'use client'
import dynamic from 'next/dynamic'

const WrappedSummary = dynamic(() => import('@/components/wrappedComponentText'), { ssr: false })

export default function WrappedPage() {
  return (
    <main className="flex items-center justify-center min-h-screen bg-pink-700">
      <WrappedSummary />
    </main>
  )
}
