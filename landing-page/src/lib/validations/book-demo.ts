import { z } from "zod";

export const bookDemoSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be under 100 characters"),
  email: z.string().email("Please enter a valid email address"),
  businessName: z
    .string()
    .min(2, "Business name must be at least 2 characters")
    .max(100, "Business name must be under 100 characters"),
  phone: z
    .string()
    .max(30, "Phone number is too long")
    .optional()
    .default(""),
  preferredDateTime: z
    .string()
    .max(100, "Preferred date/time is too long")
    .optional()
    .default(""),
  message: z
    .string()
    .max(1000, "Message must be under 1000 characters")
    .optional()
    .default(""),
});

export type BookDemoFormData = z.infer<typeof bookDemoSchema>;
