import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Contact } from "@/components/sections/Contact";

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

describe("Contact", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("renders the headline", () => {
    render(<Contact />);
    expect(screen.getByText(/Get in/)).toBeInTheDocument();
  });

  it("renders all 3 form fields", () => {
    render(<Contact />);
    expect(screen.getByLabelText("Name *")).toBeInTheDocument();
    expect(screen.getByLabelText("Email *")).toBeInTheDocument();
    expect(screen.getByLabelText("Message *")).toBeInTheDocument();
  });

  it("renders the submit button", () => {
    render(<Contact />);
    expect(
      screen.getByRole("button", { name: /send message/i })
    ).toBeInTheDocument();
  });

  it("renders contact details headings", () => {
    render(<Contact />);
    expect(screen.getByText("Email")).toBeInTheDocument();
    expect(screen.getByText("Location")).toBeInTheDocument();
  });

  it("shows validation errors on empty submit", async () => {
    const user = userEvent.setup();
    render(<Contact />);
    await user.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByText(/name must be at least 2 characters/i)).toBeInTheDocument();
    });
  });

  it("shows success message on successful submission", async () => {
    const user = userEvent.setup();
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    render(<Contact />);
    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "john@test.com");
    await user.type(screen.getByLabelText("Message *"), "I have a question about your service.");
    await user.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByText(/message sent/i)).toBeInTheDocument();
    });
  });

  it("disables button during submission", async () => {
    const user = userEvent.setup();
    mockFetch.mockImplementation(() => new Promise(() => {}));

    render(<Contact />);
    await user.type(screen.getByLabelText("Name *"), "John");
    await user.type(screen.getByLabelText("Email *"), "john@test.com");
    await user.type(screen.getByLabelText("Message *"), "Test message here.");
    await user.click(screen.getByRole("button", { name: /send message/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /sending/i })).toBeDisabled();
    });
  });
});
