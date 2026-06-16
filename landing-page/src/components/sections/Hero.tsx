"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowDown } from "lucide-react";
import { ParticleCanvas } from "@/components/effects/ParticleCanvas";
import { AnimatedOrb } from "@/components/effects/AnimatedOrb";

export function Hero() {
  return (
    <section
      id="hero"
      className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center overflow-hidden"
    >
      {/* Particle Background */}
      <ParticleCanvas />

      {/* Gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/50 to-background pointer-events-none" />

      <div className="container-nestaro relative z-10 flex flex-col items-center gap-8 lg:flex-row lg:gap-12 py-12 md:py-16 lg:py-20">
        {/* Text Content */}
        <div className="flex-1 text-center lg:text-left order-2 lg:order-1">
          <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-extrabold text-foreground leading-tight mb-6">
            Meet Nestaro —{" "}
            <span className="text-neon neon-text">Your AI Employee</span>{" "}
            That Never Sleeps
          </h1>

          <p className="text-base sm:text-lg md:text-xl text-text-secondary mb-8 max-w-xl mx-auto lg:mx-0">
            Nestaro watches your email, WhatsApp, and social media, drafts every
            reply, post, and invoice for you — and waits for your okay before
            anything goes out.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
            <Link
              href="#book-demo"
              className="inline-flex items-center justify-center rounded-lg bg-neon text-background hover:bg-neon/80 neon-glow text-base font-medium px-8 py-3 transition-colors"
            >
              Book a Free Demo
            </Link>
            <Link
              href="#how-it-works"
              className="inline-flex items-center justify-center rounded-lg border border-neon/50 text-neon hover:bg-neon/10 text-base font-medium px-8 py-3 transition-colors"
            >
              See How It Works
              <ArrowDown className="ml-2 h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* Orb Visual */}
        <div className="flex-shrink-0 flex items-center justify-center order-1 lg:order-2">
          <AnimatedOrb />
        </div>
      </div>

      {/* Scroll indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10">
        <motion.div
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <ArrowDown className="text-neon/50 h-6 w-6" />
        </motion.div>
      </div>
    </section>
  );
}
