import { render, screen } from "@testing-library/react";
import { Problem } from "@/components/sections/Problem";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe("Problem", () => {
  it("renders the headline", () => {
    render(<Problem />);
    expect(
      screen.getByText(/juggling too many channels/i)
    ).toBeInTheDocument();
  });

  it("renders the body copy", () => {
    render(<Problem />);
    expect(
      screen.getByText(/Customer emails pile up/i)
    ).toBeInTheDocument();
  });
});
