"use client";

import { ScrollReveal } from "@/components/effects/ScrollReveal";
import {
  Inbox,
  MessageCircle,
  Share2,
  Calculator,
  FileText,
  ScrollText,
} from "lucide-react";

const features = [
  {
    icon: Inbox,
    title: "Inbox management",
    description: "Reads and drafts replies to your business emails automatically.",
  },
  {
    icon: MessageCircle,
    title: "WhatsApp replies",
    description: "Drafts responses to customer messages so you never miss one.",
  },
  {
    icon: Share2,
    title: "Social media",
    description:
      "Monitors Facebook, Instagram, and Twitter/X for DMs and mentions, and drafts replies or posts.",
  },
  {
    icon: Calculator,
    title: "Accounting automation",
    description:
      "Creates invoices, records payments, and tracks your finances without manual entry.",
  },
  {
    icon: FileText,
    title: "Weekly business briefing",
    description:
      "A simple summary of what came in, what Nestaro handled, and how your finances look.",
  },
  {
    icon: ScrollText,
    title: "Full activity log",
    description:
      "A complete, searchable record of everything Nestaro has done for your business.",
  },
];

export function Features() {
  return (
    <section id="features" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="text-center mb-12 md:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-4">
              What <span className="text-neon">Nestaro</span> Can Do
            </h2>
            <p className="text-text-secondary text-base sm:text-lg max-w-2xl mx-auto">
              Everything you need to stay on top of your business communications and finances.
            </p>
          </div>
        </ScrollReveal>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {features.map((feature, index) => (
            <ScrollReveal key={feature.title} delay={index * 0.08}>
              <div className="bg-secondary rounded-2xl p-5 md:p-6 border border-secondary-light hover:border-neon/30 transition-all group h-full">
                <div className="w-12 h-12 rounded-xl bg-neon/10 flex items-center justify-center mb-4 group-hover:bg-neon/20 transition-colors">
                  <feature.icon className="w-6 h-6 text-neon" />
                </div>
                <h3 className="text-base md:text-lg font-bold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-text-secondary text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
