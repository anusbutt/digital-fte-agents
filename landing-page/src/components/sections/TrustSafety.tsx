"use client";

import Image from "next/image";
import { ScrollReveal } from "@/components/effects/ScrollReveal";

export function TrustSafety() {
  return (
    <section id="trust-safety" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="max-w-4xl mx-auto">
            <div className="relative bg-secondary rounded-2xl md:rounded-3xl p-6 md:p-8 lg:p-12 border border-neon/30 neon-border">
              {/* Shield Image */}
              <div className="flex justify-center mb-6">
                <div className="relative w-16 h-16 md:w-20 md:h-20 lg:w-24 lg:h-24">
                  <Image
                    src="/images/trust-shield.png"
                    alt="Trust & Safety Shield"
                    fill
                    sizes="(max-width: 768px) 64px, (max-width: 1024px) 80px, 96px"
                    className="object-contain drop-shadow-[0_0_15px_rgba(0,212,255,0.3)]"
                    priority
                  />
                </div>
              </div>

              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground text-center mb-6">
                Nothing happens <span className="text-neon">without you</span>.
              </h2>

              <p className="text-base sm:text-lg md:text-xl text-text-secondary leading-relaxed text-center max-w-2xl mx-auto">
                Nestaro never sends an email, posts on social media, or processes a
                payment on its own. Every single action — no matter how small — sits
                in your approval queue until you say go. Think of Nestaro as a very
                fast, very attentive assistant who drafts everything and waits for
                your signature.
              </p>

              {/* Decorative accent */}
              <div className="absolute -top-px left-1/2 -translate-x-1/2 w-32 h-[2px] bg-neon rounded-full" />
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
