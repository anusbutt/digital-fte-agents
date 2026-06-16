"use client";

import { useState } from "react";
import { ScrollReveal } from "@/components/effects/ScrollReveal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { contactSchema, type ContactFormData } from "@/lib/validations/contact";
import { CheckCircle, Loader2, Mail } from "lucide-react";

interface FormErrors {
  name?: string;
  email?: string;
  message?: string;
}

export function Contact() {
  const [formData, setFormData] = useState<ContactFormData>({
    name: "",
    email: "",
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

    const result = contactSchema.safeParse(formData);
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
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSubmitStatus("success");
        setStatusMessage("Message sent! We'll get back to you soon.");
        setFormData({ name: "", email: "", message: "" });
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
    <section id="contact" className="py-16 md:py-24 lg:py-32 relative">
      <div className="container-nestaro">
        <ScrollReveal>
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10 md:mb-12">
              <h2 className="text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold text-foreground mb-4">
                Get in <span className="text-neon">touch</span>
              </h2>
              <p className="text-text-secondary text-base sm:text-lg">
                Have a question? We&apos;d love to hear from you.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
              {/* Contact Info */}
              <div>
                <div className="bg-secondary rounded-2xl p-5 md:p-6 border border-secondary-light">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-neon/10 flex items-center justify-center shrink-0">
                      <Mail className="w-5 h-5 text-neon" />
                    </div>
                    <h3 className="text-foreground font-semibold">Email</h3>
                  </div>
                  <a
                    href="mailto:nestaropilot@gmail.com"
                    className="text-text-secondary hover:text-neon transition-colors text-sm break-all"
                  >
                    nestaropilot@gmail.com
                  </a>
                </div>
              </div>

              {/* Contact Form */}
              <div className="lg:col-span-2">
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
                    <div className="space-y-2">
                      <Label htmlFor="contact-name">Name *</Label>
                      <Input
                        id="contact-name"
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
                      <Label htmlFor="contact-email">Email *</Label>
                      <Input
                        id="contact-email"
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
                    <Label htmlFor="contact-message">Message *</Label>
                    <Textarea
                      id="contact-message"
                      name="message"
                      value={formData.message}
                      onChange={handleChange}
                      placeholder="How can we help you?"
                      rows={5}
                      className={errors.message ? "border-destructive" : ""}
                      disabled={isSubmitting}
                    />
                    {errors.message && (
                      <p className="text-destructive text-xs">{errors.message}</p>
                    )}
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
                      "Send Message"
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
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
