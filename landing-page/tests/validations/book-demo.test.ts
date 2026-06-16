import { bookDemoSchema } from "@/lib/validations/book-demo";

describe("bookDemoSchema", () => {
  const validData = {
    name: "John Doe",
    email: "john@example.com",
    businessName: "Acme Corp",
    phone: "+1 555-0123",
    preferredDateTime: "Tuesday 2pm EST",
    message: "Interested in learning more",
  };

  it("accepts valid data with all fields", () => {
    const result = bookDemoSchema.safeParse(validData);
    expect(result.success).toBe(true);
  });

  it("accepts valid data with only required fields", () => {
    const result = bookDemoSchema.safeParse({
      name: "Jane",
      email: "jane@test.com",
      businessName: "Test Co",
    });
    expect(result.success).toBe(true);
  });

  it("rejects empty name", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      name: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects name shorter than 2 characters", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      name: "A",
    });
    expect(result.success).toBe(false);
  });

  it("rejects name longer than 100 characters", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      name: "A".repeat(101),
    });
    expect(result.success).toBe(false);
  });

  it("rejects invalid email", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      email: "not-an-email",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty email", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      email: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects empty business name", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      businessName: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects business name shorter than 2 characters", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      businessName: "A",
    });
    expect(result.success).toBe(false);
  });

  it("rejects phone longer than 30 characters", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      phone: "1".repeat(31),
    });
    expect(result.success).toBe(false);
  });

  it("rejects message longer than 1000 characters", () => {
    const result = bookDemoSchema.safeParse({
      ...validData,
      message: "A".repeat(1001),
    });
    expect(result.success).toBe(false);
  });

  it("defaults optional fields to empty string", () => {
    const result = bookDemoSchema.safeParse({
      name: "John",
      email: "john@test.com",
      businessName: "Acme",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.phone).toBe("");
      expect(result.data.preferredDateTime).toBe("");
      expect(result.data.message).toBe("");
    }
  });
});
