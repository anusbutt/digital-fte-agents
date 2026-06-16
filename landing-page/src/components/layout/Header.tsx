"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

const navLinks = [
  { href: "#how-it-works", label: "How It Works" },
  { href: "#features", label: "Features" },
  { href: "#book-demo", label: "Book Demo" },
];

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-secondary">
      <div className="container-nestaro flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="w-8 h-8 rounded-lg bg-neon flex items-center justify-center">
            <span className="text-background font-bold text-sm font-mono">N</span>
          </div>
          <span className="text-xl font-bold text-foreground">Nestaro</span>
        </Link>

        {/* Desktop Nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-text-secondary hover:text-neon transition-colors text-sm font-medium"
            >
              {link.label}
            </Link>
          ))}
          <Link
            href="#book-demo"
            className="inline-flex items-center justify-center rounded-lg bg-neon text-background hover:bg-neon/80 h-9 px-4 text-sm font-medium transition-colors"
          >
            Get Started
          </Link>
        </nav>

        {/* Mobile Toggle */}
        <button
          className="md:hidden text-foreground p-2 -mr-2"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="md:hidden bg-background/95 backdrop-blur-md border-t border-secondary max-h-[calc(100vh-4rem)] overflow-y-auto">
          <nav className="container-nestaro flex flex-col py-4 gap-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="text-text-secondary hover:text-neon transition-colors text-base font-medium py-3 px-2 rounded-lg hover:bg-secondary/50"
              >
                {link.label}
              </Link>
            ))}
            <Link
              href="#book-demo"
              onClick={() => setMobileOpen(false)}
              className="inline-flex items-center justify-center rounded-lg bg-neon text-background hover:bg-neon/80 h-10 px-4 text-sm font-medium transition-colors w-full mt-2"
            >
              Get Started
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
