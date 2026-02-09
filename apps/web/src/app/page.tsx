import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-900 mb-6">
            Transform Videos into
            <span className="block text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
              Viral TikTok Clips
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Upload your long-form content and let AI create engaging, viral-ready clips
            that capture the most compelling moments automatically.
          </p>
          <div className="flex gap-4 justify-center">
            <Button asChild size="lg" className="text-lg px-8">
              <Link href="/sign-up">
                Start Creating Clips
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="text-lg px-8">
              <Link href="/sign-in">
                Sign In
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}