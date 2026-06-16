"use client";

import { ScrollReveal } from "@/components/effects/ScrollReveal";
import { Eye, FileEdit, CheckCircle2, Rocket } from "lucide-react";

const steps = [
  {
    icon: Eye,
    title: "Watch",
    description:
      "Nestaro monitors your Gmail, WhatsApp, Facebook, Instagram, Twitter/X, and accounting system around the clock.",
  },
  {
    icon: FileEdit,
    title: "Draft",
    description:
      "When something needs a reply, a post, or an accounting action (like an invoice), Nestaro prepares it for you.",
  },
  {
    icon: CheckCircle2,
    title: "Review",
    description:
      "Every draft lands in one simple approval queue. You approve, edit, or reject — nothing happens automatically.",
  },
  {
    icon: Rocket,
    title: "Done",
    description:
      "Approved items go out instantly, and everything is logged so you always have a record.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-4">
              Nestaro handles the{" "}
              <span className="text-neon">busywork</span>. You stay in control.
            </h2>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 md:gap-8">
          {steps.map((step, index) => (
            <ScrollReveal key={step.title} delay={index * 0.1}>
              <div className="relative bg-secondary rounded-2xl p-6 border border-secondary-light hover:border-neon/30 transition-colors group h-full">
                {/* Step number */}
                <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-neon text-background text-sm font-bold flex items-center justify-center">
                  {index + 1}
                </div>

                <div className="w-12 h-12 rounded-xl bg-neon/10 flex items-center justify-center mb-4 group-hover:bg-neon/20 transition-colors">
                  <step.icon className="w-6 h-6 text-neon" />
                </div>

                <h3 className="text-lg md:text-xl font-bold text-foreground mb-2">
                  {step.title}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
