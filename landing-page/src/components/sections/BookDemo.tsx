"use client";

import { useState } from "react";
import { ScrollReveal } from "@/components/effects/ScrollReveal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { bookDemoSchema, type BookDemoFormData } from "@/lib/validations/book-demo";
import { CheckCircle, Loader2, Calendar } from "lucide-react";

interface FormErrors {
  name?: string;
  email?: string;
  businessName?: string;
  phone?: string;
  preferredDateTime?: string;
  message?: string;
}

export function BookDemo() {
  const [formData, setFormData] = useState<BookDemoFormData>({
    name: "",
    email: "",
    businessName: "",
    phone: "",
    preferredDateTime: "",
    message: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");
  const [statusMessage, setStatusMessage] = useState("");

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setSubmitStatus("idle");

    const result = bookDemoSchema.safeParse(formData);
    if (!result.success) {
      const fieldErrors: FormErrors = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as keyof FormErrors;
        fieldErrors[field] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/book-demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSubmitStatus("success");
        setStatusMessage("Demo booking request sent! We'll be in touch soon.");
        setFormData({ name: "", email: "", businessName: "", phone: "", preferredDateTime: "", message: "" });
      } else {
        setSubmitStatus("error");
        setStatusMessage(
          data.message || "Something went wrong. Please try again or email us directly."
        );
      }
    } catch {
      setSubmitStatus("error");
      setStatusMessage("Something went wrong. Please try again or email us directly.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section id="book-demo" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-10 md:mb-12">
              <div className="w-14 h-14 md:w-16 md:h-16 rounded-full bg-neon/10 flex items-center justify-center mx-auto mb-4">
                <Calendar className="w-7 h-7 md:w-8 md:h-8 text-neon" />
              </div>
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-4">
                See Nestaro running on a <span className="text-neon">real business</span>
              </h2>
              <p className="text-text-secondary text-base sm:text-lg">
                Book a 20-minute call and we&apos;ll walk you through exactly how Nestaro
                would work for your business — what it watches, what it drafts, and
                how the approval process feels day to day.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Your full name"
                    className={errors.name ? "border-destructive" : ""}
                    disabled={isSubmitting}
                  />
                  {errors.name && (
                    <p className="text-destructive text-xs">{errors.name}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="you@business.com"
                    className={errors.email ? "border-destructive" : ""}
                    disabled={isSubmitting}
                  />
                  {errors.email && (
                    <p className="text-destructive text-xs">{errors.email}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="businessName">Business Name *</Label>
                <Input
                  id="businessName"
                  name="businessName"
                  value={formData.businessName}
                  onChange={handleChange}
                  placeholder="Your business name"
                  className={errors.businessName ? "border-destructive" : ""}
                  disabled={isSubmitting}
                />
                {errors.businessName && (
                  <p className="text-destructive text-xs">{errors.businessName}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone</Label>
                  <Input
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+1 (555) 000-0000"
                    disabled={isSubmitting}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="preferredDateTime">Preferred Date/Time</Label>
                  <Input
                    id="preferredDateTime"
                    name="preferredDateTime"
                    value={formData.preferredDateTime}
                    onChange={handleChange}
                    placeholder="e.g., Tuesday 2pm EST"
                    disabled={isSubmitting}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleChange}
                  placeholder="Tell us about your business and what you'd like help with..."
                  rows={4}
                  disabled={isSubmitting}
                />
              </div>

              <Button
                type="submit"
                size="lg"
                className="w-full bg-neon text-background hover:bg-neon/80 neon-glow text-base py-6"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Sending...
                  </>
                ) : (
                  "Book Your Demo"
                )}
              </Button>

              {submitStatus === "success" && (
                <div className="flex items-center gap-2 text-accent text-sm p-3 bg-accent/10 rounded-lg">
                  <CheckCircle className="h-5 w-5 flex-shrink-0" />
                  <span>{statusMessage}</span>
                </div>
              )}

              {submitStatus === "error" && (
                <p className="text-destructive text-sm p-3 bg-destructive/10 rounded-lg">
                  {statusMessage}
                </p>
              )}
            </form>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
