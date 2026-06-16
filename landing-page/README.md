# Nestaro Pilot — Landing Page

A futuristic, agentic-themed landing page for Nestaro Pilot — an AI employee for small businesses.

## Stack

- **Framework:** Next.js 14+ (App Router)
- **UI:** shadcn/ui primitives, Tailwind CSS v4
- **Animation:** Framer Motion
- **Validation:** Zod
- **Email:** Resend API
- **Icons:** Lucide React
- **Testing:** Jest + React Testing Library

## Theme

- **Background:** `#0A0A0F` (near-black)
- **Primary:** `#00D4FF` (neon blue)
- **Accent:** `#00FF88` (neon green)

## Getting Started

### Prerequisites

- Node.js 20+
- npm

### Installation

```bash
npm install
```

### Environment Variables

Copy `.env.example` to `.env.local` and fill in the values:

```bash
cp .env.example .env.local
```

| Variable | Description |
|----------|-------------|
| `RESEND_API_KEY` | Resend API key for sending form emails |
| `CONTACT_EMAIL` | Email address that receives form submissions |
| `NEXT_PUBLIC_SITE_URL` | Your site URL for OG tags |

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Build

```bash
npm run build
```

### Testing

```bash
npm test                 # Run all tests
npm run test:watch       # Watch mode
npm run test:coverage    # Coverage report
```

### Lint

```bash
npm run lint
```

## Image Generation

Generate these images using your preferred AI image generator and place them in `public/images/`:

| File | Prompt |
|------|--------|
| `hero-orb.png` | "A futuristic glowing AI core orb, translucent sphere with internal neon blue energy filaments, dark background, cinematic lighting, 4K, digital art style, no text" |
| `trust-shield.png` | "A futuristic shield icon with a checkmark, neon blue glow on dark background, minimal flat design, vector style, trustworthy and clean, no text" |
| `og-image.png` | "A futuristic AI employee concept art, dark background with neon blue accents, abstract digital brain or neural network visualization, wide format 1200x630, professional tech startup style, no text" |

## Project Structure

```
src/
├── app/
│   ├── layout.tsx          # Root layout with fonts + metadata
│   ├── page.tsx            # Single-page composition
│   ├── globals.css         # Tailwind + theme tokens + utilities
│   └── api/
│       ├── book-demo/      # Book Demo form endpoint
│       └── contact/        # Contact form endpoint
├── components/
│   ├── layout/             # Header, Footer
│   ├── sections/           # Hero, Problem, HowItWorks, Features, etc.
│   ├── ui/                 # shadcn/ui primitives
│   └── effects/            # ParticleCanvas, AnimatedOrb, GlitchText, ScrollReveal
└── lib/
    ├── utils.ts            # cn() utility
    ├── validations/        # Zod schemas
    └── email/              # Resend email service
```

## Deployment

Deployed on Vercel. Connect your repo and it auto-deploys on push.

## License

© 2026 Nestaro. All rights reserved.
