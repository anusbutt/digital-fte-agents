"use client";

import { motion } from "framer-motion";

export function AnimatedOrb() {
  return (
    <div className="relative w-44 h-44 sm:w-56 sm:h-56 md:w-64 md:h-64 lg:w-80 lg:h-80 flex items-center justify-center">
      {/* Outer glow ring */}
      <motion.div
        className="absolute inset-0 rounded-full border border-neon/30"
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 4,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      {/* Middle ring */}
      <motion.div
        className="absolute inset-4 rounded-full border border-neon/50"
        animate={{
          scale: [1, 1.08, 1],
          opacity: [0.5, 0.7, 0.5],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 0.5,
        }}
      />

      {/* Inner core */}
      <motion.div
        className="absolute inset-10 sm:inset-12 rounded-full bg-neon/20 neon-glow"
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.4, 0.7, 0.4],
        }}
        transition={{
          duration: 2.5,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1,
        }}
      />

      {/* Core center */}
      <motion.div
        className="absolute inset-16 sm:inset-20 rounded-full bg-neon/40"
        animate={{
          scale: [1, 1.15, 1],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut",
          delay: 1.5,
        }}
      />

      {/* Center dot */}
      <div className="absolute w-4 h-4 rounded-full bg-neon neon-glow" />

      {/* Orbiting particles */}
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="absolute w-2 h-2 rounded-full bg-neon/60"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 6 + i * 2,
            repeat: Infinity,
            ease: "linear",
            delay: i * 0.8,
          }}
          style={{
            transformOrigin: "center center",
            left: "50%",
            top: "50%",
            marginLeft: "-4px",
            marginTop: "-4px",
            transform: `rotate(${i * 120}deg) translateX(${70 + i * 10}px)`,
          }}
        />
      ))}
    </div>
  );
}
