import { render, screen } from "@testing-library/react";
import { HowItWorks } from "@/components/sections/HowItWorks";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, delay, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe("HowItWorks", () => {
  it("renders the headline", () => {
    render(<HowItWorks />);
    expect(
      screen.getByText(/Nestaro handles the/i)
    ).toBeInTheDocument();
  });

  it("renders all 4 steps", () => {
    render(<HowItWorks />);
    expect(screen.getByText("Watch")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Review")).toBeInTheDocument();
    expect(screen.getByText("Done")).toBeInTheDocument();
  });

  it("renders step descriptions", () => {
    render(<HowItWorks />);
    expect(
      screen.getByText(/monitors your Gmail, WhatsApp/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/prepares it for you/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/approval queue/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/go out instantly/i)
    ).toBeInTheDocument();
  });
});
