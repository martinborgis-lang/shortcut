import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Terms of Service - ShortCut",
  description: "ShortCut's Terms of Service - Rules and guidelines for using our AI video clipping platform.",
  robots: {
    index: true,
    follow: true,
  },
}

export default function TermsOfServicePage() {
  return (
    <div className="py-24">
      <div className="section-container">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="space-y-4">
            <h1 className="text-4xl font-bold text-white">Terms of Service</h1>
            <p className="text-muted-foreground">
              Last updated: December 1, 2024
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-invert prose-lg max-w-none">
            <div className="space-y-8 text-muted-foreground">
              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Acceptance of Terms</h2>
                <p>
                  By accessing and using ShortCut ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Description of Service</h2>
                <p>
                  ShortCut is an AI-powered video clipping service that helps content creators transform long-form videos into short, engaging clips optimized for social media platforms like TikTok, Instagram, and YouTube Shorts.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">User Accounts and Responsibilities</h2>
                <div className="space-y-4">
                  <p>To use our service, you must:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>Be at least 13 years old</li>
                    <li>Provide accurate and complete information when creating an account</li>
                    <li>Maintain the security of your account credentials</li>
                    <li>Accept responsibility for all activities under your account</li>
                    <li>Notify us immediately of any unauthorized use</li>
                  </ul>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Content and Intellectual Property</h2>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white">Your Content</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>You retain ownership of videos and content you upload</li>
                      <li>You grant us a limited license to process your content using our AI technology</li>
                      <li>You must have the right to use and share the content you upload</li>
                      <li>You are responsible for ensuring your content doesn't infringe on others' rights</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">Our Service</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>ShortCut and our AI technology are our intellectual property</li>
                      <li>You may not reverse engineer, copy, or distribute our service</li>
                      <li>Generated clips are yours to use, but our processing technology remains ours</li>
                    </ul>
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Acceptable Use Policy</h2>
                <p>You agree not to use ShortCut to:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Upload content that is illegal, harmful, or violates others' rights</li>
                  <li>Create content that promotes hate speech, violence, or discrimination</li>
                  <li>Impersonate others or misrepresent your identity</li>
                  <li>Attempt to hack, disrupt, or overload our systems</li>
                  <li>Use our service for any commercial purpose without permission</li>
                  <li>Share your account with others or create multiple accounts</li>
                </ul>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Subscription and Billing</h2>
                <div className="space-y-4">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Subscriptions are billed in advance on a monthly or annual basis</li>
                    <li>All fees are non-refundable except as required by law</li>
                    <li>We may change pricing with 30 days notice to existing subscribers</li>
                    <li>Your subscription will auto-renew unless you cancel before the renewal date</li>
                    <li>You can cancel your subscription at any time from your account settings</li>
                  </ul>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Service Availability and Limitations</h2>
                <p>
                  We strive to provide reliable service but cannot guarantee 100% uptime. We may temporarily suspend service for maintenance, updates, or other operational needs.
                </p>
                <p>
                  Processing limits apply based on your subscription tier. We reserve the right to limit usage that we determine to be excessive or abusive.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Limitation of Liability</h2>
                <p>
                  ShortCut provides the service "as is" without any warranties. We are not liable for any damages arising from your use of our service, including but not limited to lost profits, data loss, or service interruptions.
                </p>
                <p>
                  Our total liability to you for any claims related to our service will not exceed the amount you paid us in the 12 months preceding the claim.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Termination</h2>
                <p>
                  We may suspend or terminate your account if you violate these terms or engage in activities that harm our service or other users. Upon termination, your access to the service will cease, and we may delete your account and associated data.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Changes to Terms</h2>
                <p>
                  We may update these Terms of Service from time to time. We will notify you of any significant changes by email or through our service. Continued use of ShortCut after changes constitutes acceptance of the new terms.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Governing Law</h2>
                <p>
                  These terms are governed by the laws of [Jurisdiction]. Any disputes will be resolved in the courts of [Jurisdiction].
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Contact Information</h2>
                <p>
                  If you have questions about these Terms of Service, please contact us at:
                </p>
                <div className="bg-card/50 rounded-lg p-4 border border-border">
                  <p>Email: legal@shortcut.app</p>
                  <p>Address: [Company Address]</p>
                </div>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}