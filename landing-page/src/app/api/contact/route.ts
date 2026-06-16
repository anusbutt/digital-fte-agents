import { NextRequest, NextResponse } from "next/server";
import { contactSchema } from "@/lib/validations/contact";
import { sendEmail } from "@/lib/email/resend";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const result = contactSchema.safeParse(body);

    if (!result.success) {
      const errors: Record<string, string> = {};
      for (const issue of result.error.issues) {
        const field = issue.path[0] as string;
        if (!errors[field]) {
          errors[field] = issue.message;
        }
      }
      return NextResponse.json(
        { success: false, errors },
        { status: 400 }
      );
    }

    const { name, email, message } = result.data;
    const contactEmail = process.env.CONTACT_EMAIL || "nestaropilot@gmail.com";

    const html = `
      <h2>New Contact Message</h2>
      <p><strong>Name:</strong> ${name}</p>
      <p><strong>Email:</strong> ${email}</p>
      <p><strong>Message:</strong></p>
      <p>${message.replace(/\n/g, "<br />")}</p>
      <hr />
      <p>Submitted at: ${new Date().toISOString()}</p>
    `;

    const emailResult = await sendEmail({
      to: contactEmail,
      subject: `Contact from ${name}`,
      html,
    });

    if (!emailResult.success) {
      return NextResponse.json(
        {
          success: false,
          message: "Something went wrong. Please try again or email us directly.",
        },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { success: true, message: "Message sent!" },
      { status: 200 }
    );
  } catch {
    return NextResponse.json(
      {
        success: false,
        message: "Something went wrong. Please try again or email us directly.",
      },
      { status: 500 }
    );
  }
}
