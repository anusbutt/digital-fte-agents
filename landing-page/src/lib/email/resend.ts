interface SendEmailParams {
  to: string;
  subject: string;
  html: string;
}

export async function sendEmail({
  to,
  subject,
  html,
}: SendEmailParams): Promise<{ success: boolean; error?: string }> {
  const apiKey = process.env.RESEND_API_KEY;

  if (!apiKey) {
    console.error("RESEND_API_KEY is not configured");
    return { success: false, error: "Email service not configured" };
  }

  // Build a valid "from" address — must be either "email@domain.com" or "Name <email@domain.com>"
  const rawFrom = process.env.RESEND_FROM_EMAIL?.trim();
  let from: string;
  if (rawFrom && rawFrom.includes("<") && rawFrom.includes(">")) {
    // Already in "Name <email>" format
    from = rawFrom;
  } else if (rawFrom && rawFrom.includes("@")) {
    // Plain email — wrap it
    from = rawFrom;
  } else {
    // Fallback to Resend's test sender
    from = "onboarding@resend.dev";
  }

  console.log("Resend send:", { from, to, subject, hasKey: !!apiKey });

  try {
    const response = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ from, to, subject, html }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage =
        (errorData as { message?: string }).message ||
        `Resend API error ${response.status}`;
      console.error("Resend API error:", response.status, errorData);
      return { success: false, error: errorMessage };
    }

    return { success: true };
  } catch (error) {
    console.error("Email send error:", error);
    return { success: false, error: "Failed to send email" };
  }
}
