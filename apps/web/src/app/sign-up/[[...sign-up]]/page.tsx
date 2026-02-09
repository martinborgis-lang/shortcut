import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900">
      <SignUp
        appearance={{
          elements: {
            formButtonPrimary: 'bg-[#E94560] hover:bg-[#E94560]/90 text-sm',
            card: 'shadow-lg bg-[#1A1A2E] border-[#2A2A3E]',
            headerTitle: 'text-white',
            headerSubtitle: 'text-gray-400',
            socialButtonsBlockButton: 'bg-[#2A2A3E] border-[#2A2A3E] text-white hover:bg-[#3A3A4E]',
            formFieldInput: 'bg-[#0F0F1A] border-[#2A2A3E] text-white',
            formFieldLabel: 'text-gray-300',
            footerActionText: 'text-gray-400',
            footerActionLink: 'text-[#E94560]',
          }
        }}
        fallbackRedirectUrl="/dashboard"
      />
    </div>
  )
}