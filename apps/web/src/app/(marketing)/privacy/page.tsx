import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Privacy Policy - ShortCut",
  description: "ShortCut's Privacy Policy - How we collect, use, and protect your personal information.",
  robots: {
    index: true,
    follow: true,
  },
}

export default function PrivacyPolicyPage() {
  return (
    <div className="py-24">
      <div className="section-container">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <div className="space-y-4">
            <h1 className="text-4xl font-bold text-white">Privacy Policy</h1>
            <p className="text-muted-foreground">
              Last updated: December 1, 2024
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-invert prose-lg max-w-none">
            <div className="space-y-8 text-muted-foreground">
              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Introduction</h2>
                <p>
                  ShortCut (&ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;) is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our AI-powered video clipping service.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Information We Collect</h2>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white">Personal Information</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>Name and email address when you create an account</li>
                      <li>Billing information for paid subscriptions</li>
                      <li>Profile information you choose to provide</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">Content Information</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>Videos you upload or link for processing</li>
                      <li>Generated clips and associated metadata</li>
                      <li>User preferences and customizations</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">Usage Information</h3>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      <li>How you interact with our service</li>
                      <li>Device and browser information</li>
                      <li>IP address and location data</li>
                    </ul>
                  </div>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">How We Use Your Information</h2>
                <ul className="list-disc list-inside space-y-1">
                  <li>To provide and improve our video clipping service</li>
                  <li>To process your videos using our AI technology</li>
                  <li>To manage your account and billing</li>
                  <li>To send important service communications</li>
                  <li>To provide customer support</li>
                  <li>To analyze usage patterns and improve our algorithms</li>
                </ul>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Data Storage and Security</h2>
                <p>
                  We implement industry-standard security measures to protect your information. Your videos are processed securely and stored temporarily only for the duration needed to generate clips. We use encryption in transit and at rest.
                </p>
                <p>
                  Processed videos are automatically deleted from our servers after 30 days unless you choose to keep them in your account library.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Third-Party Services</h2>
                <p>
                  We may use third-party services for:
                </p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Payment processing (Stripe)</li>
                  <li>Analytics (Google Analytics)</li>
                  <li>Authentication (Clerk)</li>
                  <li>Cloud storage and processing (AWS, Google Cloud)</li>
                  <li>Social media integration (TikTok, Instagram, YouTube APIs)</li>
                </ul>
                <p>
                  These services have their own privacy policies and may collect information independently.
                </p>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Your Rights</h2>
                <p>You have the right to:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Access your personal information</li>
                  <li>Correct inaccurate information</li>
                  <li>Delete your account and associated data</li>
                  <li>Export your data</li>
                  <li>Opt out of marketing communications</li>
                  <li>Request restriction of processing</li>
                </ul>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Contact Us</h2>
                <p>
                  If you have questions about this Privacy Policy, please contact us at:
                </p>
                <div className="bg-card/50 rounded-lg p-4 border border-border">
                  <p>Email: privacy@shortcut.app</p>
                  <p>Address: [Company Address]</p>
                </div>
              </section>

              <section className="space-y-4">
                <h2 className="text-2xl font-semibold text-white">Changes to This Policy</h2>
                <p>
                  We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the &ldquo;Last updated&rdquo; date.
                </p>
              </section>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}