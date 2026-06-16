/**
 * @jest-environment node
 */

import { POST } from "@/app/api/contact/route";
import { NextRequest } from "next/server";

jest.mock("@/lib/email/resend", () => ({
  sendEmail: jest.fn(),
}));

import { sendEmail } from "@/lib/email/resend";
const mockSendEmail = sendEmail as jest.MockedFunction<typeof sendEmail>;

function createRequest(body: object): NextRequest {
  return new NextRequest("http://localhost:3000/api/contact", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/contact", () => {
  beforeEach(() => {
    mockSendEmail.mockReset();
  });

  const validPayload = {
    name: "Jane Doe",
    email: "jane@example.com",
    message: "I have a question about Nestaro.",
  };

  it("returns 200 with success for valid payload", async () => {
    mockSendEmail.mockResolvedValueOnce({ success: true });

    const response = await POST(createRequest(validPayload));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.success).toBe(true);
    expect(data.message).toBe("Message sent!");
  });

  it("returns 400 for invalid email", async () => {
    const response = await POST(
      createRequest({ ...validPayload, email: "not-email" })
    );
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.success).toBe(false);
    expect(data.errors).toHaveProperty("email");
  });

  it("returns 400 for empty required fields", async () => {
    const response = await POST(
      createRequest({ ...validPayload, name: "", message: "" })
    );
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.success).toBe(false);
    expect(data.errors).toHaveProperty("name");
    expect(data.errors).toHaveProperty("message");
  });

  it("returns 400 for message too short", async () => {
    const response = await POST(
      createRequest({ ...validPayload, message: "Short" })
    );
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.errors).toHaveProperty("message");
  });

  it("returns 500 when email service fails", async () => {
    mockSendEmail.mockResolvedValueOnce({
      success: false,
      error: "Failed",
    });

    const response = await POST(createRequest(validPayload));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.success).toBe(false);
    expect(data.message).toContain("try again");
  });

  it("returns 500 on unexpected error", async () => {
    mockSendEmail.mockRejectedValueOnce(new Error("Network error"));

    const response = await POST(createRequest(validPayload));
    const data = await response.json();

    expect(response.status).toBe(500);
    expect(data.success).toBe(false);
  });
});
