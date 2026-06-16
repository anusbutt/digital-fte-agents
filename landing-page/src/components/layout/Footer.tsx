import Link from "next/link";
import { Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-secondary border-t border-secondary-light mt-auto">
      <div className="container-nestaro py-10 md:py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="sm:col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-neon flex items-center justify-center">
                <span className="text-background font-bold text-sm font-mono">N</span>
              </div>
              <span className="text-xl font-bold text-foreground">Nestaro</span>
            </div>
            <p className="text-text-secondary text-sm">
              Your AI employee that never sleeps. Automating busywork for small businesses.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-foreground font-semibold mb-4">Quick Links</h3>
            <nav className="flex flex-col gap-2">
              <Link href="#how-it-works" className="text-text-secondary hover:text-neon transition-colors text-sm">
                How It Works
              </Link>
              <Link href="#features" className="text-text-secondary hover:text-neon transition-colors text-sm">
                Features
              </Link>
              <Link href="#book-demo" className="text-text-secondary hover:text-neon transition-colors text-sm">
                Book a Demo
              </Link>
              <Link href="#contact" className="text-text-secondary hover:text-neon transition-colors text-sm">
                Contact
              </Link>
            </nav>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-foreground font-semibold mb-4">Contact</h3>
            <div className="flex items-center gap-2 text-text-secondary text-sm">
              <Mail size={16} className="text-neon shrink-0" />
              <a href="mailto:nestaropilot@gmail.com" className="hover:text-neon transition-colors break-all">
                nestaropilot@gmail.com
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-secondary-light mt-8 pt-8 text-center">
          <p className="text-text-secondary text-sm">
            © {new Date().getFullYear()} Nestaro. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
