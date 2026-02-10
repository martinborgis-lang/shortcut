import { SignIn } from '@clerk/nextjs'

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950">
      <div className="absolute inset-0">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)',
            backgroundSize: '60px 60px',
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-purple-600/20 via-transparent to-cyan-500/20" />
      </div>
      <div className="relative z-10">
      <SignIn
        appearance={{
          elements: {
            formButtonPrimary: 'bg-gradient-to-r from-purple-600 to-cyan-500 hover:from-purple-700 hover:to-cyan-600 text-sm',
            card: 'shadow-lg bg-zinc-900/50 backdrop-blur-sm border border-white/10',
            headerTitle: 'text-white',
            headerSubtitle: 'text-gray-400',
            socialButtonsBlockButton: 'bg-zinc-800 border-white/10 text-white hover:bg-zinc-700',
            formFieldInput: 'bg-zinc-800 border-white/10 text-white',
            formFieldLabel: 'text-gray-300',
            footerActionText: 'text-gray-400',
            footerActionLink: 'text-purple-400',
          }
        }}
        fallbackRedirectUrl="/dashboard"
      />
      </div>
    </div>
  )
}