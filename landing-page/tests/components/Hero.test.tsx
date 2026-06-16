import { render, screen } from "@testing-library/react";
import { Hero } from "@/components/sections/Hero";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { animate, transition, initial, whileInView, viewport, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

jest.mock("@/components/effects/ParticleCanvas", () => ({
  ParticleCanvas: () => <div data-testid="particle-canvas" />,
}));

jest.mock("@/components/effects/AnimatedOrb", () => ({
  AnimatedOrb: () => <div data-testid="animated-orb" />,
}));

describe("Hero", () => {
  it("renders the main headline", () => {
    render(<Hero />);
    expect(
      screen.getByText(/Meet Nestaro/i)
    ).toBeInTheDocument();
  });

  it("renders the subheadline", () => {
    render(<Hero />);
    expect(
      screen.getByText(/watches your email, WhatsApp, and social media/i)
    ).toBeInTheDocument();
  });

  it("renders the primary CTA button", () => {
    render(<Hero />);
    expect(
      screen.getByRole("link", { name: /book a free demo/i })
    ).toBeInTheDocument();
  });

  it("renders the secondary CTA button", () => {
    render(<Hero />);
    expect(
      screen.getByRole("link", { name: /see how it works/i })
    ).toBeInTheDocument();
  });

  it("renders the animated orb", () => {
    render(<Hero />);
    expect(screen.getByTestId("animated-orb")).toBeInTheDocument();
  });

  it("renders the particle canvas", () => {
    render(<Hero />);
    expect(screen.getByTestId("particle-canvas")).toBeInTheDocument();
  });
});
