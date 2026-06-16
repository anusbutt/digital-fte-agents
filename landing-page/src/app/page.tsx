import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { Hero } from "@/components/sections/Hero";
import { Problem } from "@/components/sections/Problem";
import { HowItWorks } from "@/components/sections/HowItWorks";
import { Features } from "@/components/sections/Features";
import { TrustSafety } from "@/components/sections/TrustSafety";
import { GettingStarted } from "@/components/sections/GettingStarted";
import { BookDemo } from "@/components/sections/BookDemo";
import { Contact } from "@/components/sections/Contact";

export default function Home() {
  return (
    <>
      <Header />
      <main className="flex-1 pt-16">
        <Hero />
        <Problem />
        <HowItWorks />
        <Features />
        <TrustSafety />
        <GettingStarted />
        <BookDemo />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
