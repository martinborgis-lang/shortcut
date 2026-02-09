import Navbar from '@/components/landing/Navbar';
import Hero from '@/components/landing/Hero';
import SocialProof from '@/components/landing/SocialProof';
import FeatureTabs from '@/components/landing/FeatureTabs';
import HowItWorks from '@/components/landing/HowItWorks';
import Stats from '@/components/landing/Stats';
import Testimonials from '@/components/landing/Testimonials';
import Pricing from '@/components/landing/Pricing';
import FAQ from '@/components/landing/FAQ';
import FinalCTA from '@/components/landing/FinalCTA';
import Footer from '@/components/landing/Footer';

export default function Home() {
  return (
    <div className="w-full min-h-screen overflow-x-hidden bg-zinc-950 text-white">
      <Navbar />
      <main className="w-full">
        <Hero />
        <SocialProof />
        <FeatureTabs />
        <HowItWorks />
        <Stats />
        <Testimonials />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>
      <Footer />
    </div>
  );
}