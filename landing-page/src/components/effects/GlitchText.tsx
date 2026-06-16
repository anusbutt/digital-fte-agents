"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlitchTextProps {
  children: ReactNode;
  className?: string;
  as?: "h1" | "h2" | "h3" | "span" | "p";
}

export function GlitchText({
  children,
  className = "",
  as: Tag = "h2",
}: GlitchTextProps) {
  return (
    <div className={`relative inline-block ${className}`}>
      {/* Main text */}
      <Tag className="relative z-10">{children}</Tag>

      {/* Glitch layers */}
      <motion.span
        className="absolute inset-0 text-neon/70 z-0"
        aria-hidden="true"
        initial={{ opacity: 0, x: 0 }}
        whileInView={{ opacity: [0, 0.8, 0, 0.6, 0], x: [0, -3, 2, -1, 0] }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, delay: 0.1, ease: "easeOut" }}
        style={{ clipPath: "inset(20% 0 40% 0)" }}
      >
        {children}
      </motion.span>

      <motion.span
        className="absolute inset-0 text-accent/50 z-0"
        aria-hidden="true"
        initial={{ opacity: 0, x: 0 }}
        whileInView={{ opacity: [0, 0.6, 0, 0.4, 0], x: [0, 3, -2, 1, 0] }}
        viewport={{ once: true }}
        transition={{ duration: 0.35, delay: 0.15, ease: "easeOut" }}
        style={{ clipPath: "inset(50% 0 10% 0)" }}
      >
        {children}
      </motion.span>
    </div>
  );
}
