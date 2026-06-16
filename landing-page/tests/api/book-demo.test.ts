/**
 * @jest-environment node
 */

import { POST } from "@/app/api/book-demo/route";
import { NextRequest } from "next/server";

// Mock the email module
jest.mock("@/lib/email/resend", () => ({
  sendEmail: jest.fn(),
}));

import { sendEmail } from "@/lib/email/resend";
const mockSendEmail = sendEmail as jest.MockedFunction<typeof sendEmail>;

function createRequest(body: object): NextRequest {
  return new NextRequest("http://localhost:3000/api/book-demo", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

describe("POST /api/book-demo", () => {
  beforeEach(() => {
    mockSendEmail.mockReset();
  });

  const validPayload = {
    name: "John Doe",
    email: "john@example.com",
    businessName: "Acme Corp",
    phone: "+1 555-0123",
    preferredDateTime: "Tuesday 2pm",
    message: "Interested!",
  };

  it("returns 200 with success for valid payload", async () => {
    mockSendEmail.mockResolvedValueOnce({ success: true });

    const response = await POST(createRequest(validPayload));
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.success).toBe(true);
    expect(data.message).toBe("Demo booking request sent!");
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
      createRequest({ ...validPayload, name: "", businessName: "" })
    );
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.success).toBe(false);
    expect(data.errors).toHaveProperty("name");
    expect(data.errors).toHaveProperty("businessName");
  });

  it("returns 400 for name too short", async () => {
    const response = await POST(
      createRequest({ ...validPayload, name: "A" })
    );
    const data = await response.json();

    expect(response.status).toBe(400);
    expect(data.errors).toHaveProperty("name");
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
