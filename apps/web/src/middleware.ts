// Middleware temporaire - Clerk désactivé pour le moment
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Pour l'instant, on laisse passer toutes les requêtes
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
}