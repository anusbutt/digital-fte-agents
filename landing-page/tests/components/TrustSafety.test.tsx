import { render, screen } from "@testing-library/react";
import { TrustSafety } from "@/components/sections/TrustSafety";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe("TrustSafety", () => {
  it("renders the headline", () => {
    render(<TrustSafety />);
    expect(
      screen.getByText(/Nothing happens/i)
    ).toBeInTheDocument();
  });

  it("renders the trust message body", () => {
    render(<TrustSafety />);
    expect(
      screen.getByText(/never sends an email/i)
    ).toBeInTheDocument();
  });

  it("renders the approval queue message", () => {
    render(<TrustSafety />);
    expect(
      screen.getByText(/approval queue until you say go/i)
    ).toBeInTheDocument();
  });
});
