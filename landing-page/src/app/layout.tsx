import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000"),
  title: "Nestaro — Your AI Employee That Never Sleeps",
  description:
    "Nestaro watches your email, WhatsApp, and social media, drafts every reply, post, and invoice for you — and waits for your okay before anything goes out.",
  openGraph: {
    title: "Nestaro — Your AI Employee That Never Sleeps",
    description:
      "Nestaro watches your email, WhatsApp, and social media, drafts every reply, post, and invoice for you — and waits for your okay before anything goes out.",
    type: "website",
    url: process.env.NEXT_PUBLIC_SITE_URL || "https://nestaro.ai",
    images: [
      {
        url: "/images/og-image.png",
        width: 1200,
        height: 630,
        alt: "Nestaro — AI Employee for Small Businesses",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Nestaro — Your AI Employee That Never Sleeps",
    description:
      "Nestaro watches your email, WhatsApp, and social media, drafts every reply, post, and invoice for you — and waits for your okay before anything goes out.",
    images: ["/images/og-image.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} dark`}
    >
      <body className="min-h-screen flex flex-col antialiased">
        {children}
      </body>
    </html>
  );
}
