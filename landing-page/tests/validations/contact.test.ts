import { contactSchema } from "@/lib/validations/contact";

describe("contactSchema", () => {
  const validData = {
    name: "John Doe",
    email: "john@example.com",
    message: "I have a question about Nestaro and how it works.",
  };

  it("accepts valid data", () => {
    const result = contactSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  it("rejects empty name", () => {
    const result = contactSchema.safeParse({
      ...validData,
      name: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects name shorter than 2 characters", () => {
    const result = contactSchema.safeParse({
      ...validData,
      name: "A",
    });
    expect(result.success).toBe(false);
  });

  it("rejects name longer than 100 characters", () => {
    const result = contactSchema.safeParse({
      ...validData,
      name: "A".repeat(101),
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid email", () => {
    const result = contactSchema.safeParse({
      ...validData,
      email: "not-an-email",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty email", () => {
    const result = contactSchema.safeParse({
      ...validData,
      email: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects message shorter than 10 characters", () => {
    const result = contactSchema.safeParse({
      ...validData,
      message: "Short",
    });
    expect(result.success).toBe(false);
  });

  it("rejects message longer than 2000 characters", () => {
    const result = contactSchema.safeParse({
      ...validData,
      message: "A".repeat(2001),
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty message", () => {
    const result = contactSchema.safeParse({
      ...validData,
      message: "",
    });
    expect(result.success).toBe(false);
  });
});
