import { render, screen } from "@testing-library/react";
import { GettingStarted } from "@/components/sections/GettingStarted";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, delay, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe("GettingStarted", () => {
  it("renders the headline", () => {
    render(<GettingStarted />);
    expect(
      screen.getByText(/Up and running/i)
    ).toBeInTheDocument();
  });

  it("renders all 4 steps", () => {
    render(<GettingStarted />);
    expect(screen.getByText("Connect your accounts")).toBeInTheDocument();
    expect(screen.getByText("Nestaro starts watching")).toBeInTheDocument();
    expect(screen.getByText("Check your queue")).toBeInTheDocument();
    expect(screen.getByText("Get your weekly briefing")).toBeInTheDocument();
  });
});
