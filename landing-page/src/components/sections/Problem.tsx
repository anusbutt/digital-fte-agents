"use client";

import { ScrollReveal } from "@/components/effects/ScrollReveal";

export function Problem() {
  return (
    <section id="problem" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-6">
              Running a small business means{" "}
              <span className="text-neon">juggling too many channels</span>
            </h2>
            <p className="text-base sm:text-lg md:text-xl text-text-secondary leading-relaxed">
              Customer emails pile up. WhatsApp messages sit unanswered for hours.
              Comments and DMs on Facebook, Instagram, and Twitter/X get missed. Invoices
              and bookkeeping fall behind while you&apos;re busy actually running the
              business. You can&apos;t be everywhere at once — and hiring someone to
              watch it all is expensive and slow to train.
            </p>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
