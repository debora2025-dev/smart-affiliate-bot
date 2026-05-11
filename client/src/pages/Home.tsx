import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import Plans from '@/components/Plans';
import Calculator from '@/components/Calculator';
import PlansComparison from '@/components/PlansComparison';
import DriverRules from '@/components/DriverRules';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Hero />
        <Features />
        <Plans />
        <Calculator />
        <PlansComparison />
        <DriverRules />
      </main>
      <Footer />
    </div>
  );
}
