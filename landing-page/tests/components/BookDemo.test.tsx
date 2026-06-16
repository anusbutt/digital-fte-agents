import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BookDemo } from "@/components/sections/BookDemo";

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => {
      const { initial, whileInView, viewport, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("BookDemo", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders the headline", () => {
    render(<BookDemo />);
    expect(
      screen.getByText(/See Nestaro running on a/i)
    ).toBeInTheDocument();
  });

  it("renders all 6 form fields", () => {
    render(<BookDemo />);
    expect(screen.getByLabelText("Name *")).toBeInTheDocument();
    expect(screen.getByLabelText("Email *")).toBeInTheDocument();
    expect(screen.getByLabelText("Business Name *")).toBeInTheDocument();
    expect(screen.getByLabelText("Phone")).toBeInTheDocument();
    expect(screen.getByLabelText("Preferred Date/Time")).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });

  it("renders the submit button", () => {
    render(<BookDemo />);
    expect(
      screen.getByRole("button", { name: /book your demo/i })
    ).toBeInTheDocument();
  });

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup();
    render(<BookDemo />);
    await user.click(screen.getByRole("button", { name: /book your demo/i }));

    await waitFor(() => {
      expect(
        screen.queryAllByText("Name must be at least 2 characters").length
      ).toBeGreaterThan(0);
    });
  });

  it("keeps invalid email visible for correction", async () => {
    const user = userEvent.setup();
    render(<BookDemo />);

    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "not-email");
    await user.type(screen.getByLabelText("Business Name *"), "Acme");
    await user.click(screen.getByRole("button", { name: /book your demo/i }));

    await waitFor(() => {
      expect(screen.getByLabelText("Email *")).toHaveValue("not-email");
    });
  });

  it("disables button during submission", async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<BookDemo />);
    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "john@test.com");
    await user.type(screen.getByLabelText("Business Name *"), "Acme");
    await user.click(screen.getByRole("button", { name: /book your demo/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();
    });
  });

  it("shows success message on successful submission", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    render(<BookDemo />);
    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "john@test.com");
    await user.type(screen.getByLabelText("Business Name *"), "Acme");
    await user.click(screen.getByRole("button", { name: /book your demo/i }));

    await waitFor(() => {
      expect(screen.getByText(/demo booking request sent/i)).toBeInTheDocument();
    });
  });

  it("re-enables submit button after API failure", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ message: "Server error" }),
    });

    render(<BookDemo />);
    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "john@test.com");
    await user.type(screen.getByLabelText("Business Name *"), "Acme");
    await user.click(screen.getByRole("button", { name: /book your demo/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /book your demo/i })).not.toBeDisabled();
    });
  });
});
