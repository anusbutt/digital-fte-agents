import { render, screen } from "@testing-library/react";
import { Features } from "@/components/sections/Features";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe("Features", () => {
  it("renders the headline", () => {
    render(<Features />);
    expect(
      screen.getByRole("heading", {
        name: (content) => content.includes("What") && content.includes("Nestaro") && content.includes("Can Do"),
      })
    ).toBeInTheDocument();
  });

  it("renders all 6 feature cards", () => {
    render(<Features />);
    expect(screen.getByText("Inbox management")).toBeInTheDocument();
    expect(screen.getByText("WhatsApp replies")).toBeInTheDocument();
    expect(screen.getByText("Social media")).toBeInTheDocument();
    expect(screen.getByText("Accounting automation")).toBeInTheDocument();
    expect(screen.getByText("Weekly business briefing")).toBeInTheDocument();
    expect(screen.getByText("Full activity log")).toBeInTheDocument();
  });
});
