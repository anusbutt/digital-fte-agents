import { NextRequest, NextResponse } from "next/server";
import { bookDemoSchema } from "@/lib/validations/book-demo";
import { sendEmail } from "@/lib/email/resend";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const result = bookDemoSchema.safeParse(body);

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

    const { name, email, businessName, phone, preferredDateTime, message } = result.data;
    const contactEmail = process.env.CONTACT_EMAIL || "nestaropilot@gmail.com";

    const html = `
      <h2>New Demo Booking Request</h2>
      <p><strong>Name:</strong> ${name}</p>
      <p><strong>Email:</strong> ${email}</p>
      <p><strong>Business:</strong> ${businessName}</p>
      ${phone ? `<p><strong>Phone:</strong> ${phone}</p>` : ""}
      ${preferredDateTime ? `<p><strong>Preferred Date/Time:</strong> ${preferredDateTime}</p>` : ""}
      ${message ? `<p><strong>Message:</strong> ${message}</p>` : ""}
      <hr />
      <p>Submitted at: ${new Date().toISOString()}</p>
    `;

    const emailResult = await sendEmail({
      to: contactEmail,
      subject: `Demo Request from ${name} (${businessName})`,
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
      { success: true, message: "Demo booking request sent!" },
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
