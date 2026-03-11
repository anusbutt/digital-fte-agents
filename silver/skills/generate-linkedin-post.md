# Skill: Generate LinkedIn Post

## Purpose

Generate a professional LinkedIn post about AI automation, digital FTEs, or industry insights. The post is created in `/Pending_Approval/` for human review before publishing. LinkedIn posts **always require approval**.

## Instructions

You are the AI Employee. Follow these steps precisely:

### Step 1: Gather Context

Read `Business_Goals.md` from the vault root to understand:
- Current business focus and strategy
- Key themes and messaging priorities
- Industry positioning

Read `Company_Handbook.md` for:
- Communication tone and brand voice
- Any LinkedIn-specific guidelines

Optionally read recent entries in `Briefings/` for timely topics.

### Step 2: Choose a Topic

Select one topic from these categories (rotate to avoid repetition):
- **AI Automation**: How AI assistants improve business operations
- **Digital FTEs**: The concept of AI employees and their capabilities
- **Industry Insights**: Trends in AI, automation, and business productivity
- **Lessons Learned**: Practical takeaways from implementing AI solutions
- **Future of Work**: How AI and humans collaborate effectively

Check `Pending_Approval/` and `Done/` for recent `LINKEDIN_*.md` files to avoid repeating topics.

### Step 3: Write the Post

Compose a LinkedIn post following these rules:
- **Length**: 150-300 words (optimal for LinkedIn engagement)
- **Structure**: Hook line → Body → Call to action
- **Tone**: Professional but personable, thought-leadership style
- **Format**: Use line breaks for readability, optionally 1-2 relevant emojis
- **Hashtags**: Include 3-5 relevant hashtags at the end
- Never mention internal processes, AI tools by name, or company secrets
- Never use overly promotional language
- Focus on providing value and insights to the audience

### Step 4: Create LinkedIn Post File

Create `LINKEDIN_{YYYY-MM-DD}.md` in `/Pending_Approval/` with this exact structure:

```yaml
---
type: linkedin_post
content: "{Full post text}"
topic: "{AI automation | digital FTEs | industry insights | lessons learned | future of work}"
generated_date: {current ISO 8601 timestamp}
status: pending
posted_date: null
---

## LinkedIn Post

{Post content with formatting}

## To Approve

Move this file to the `/Approved/` folder.

## To Reject

Move this file to the `/Rejected/` folder.
```

### Step 5: Log the Result

Log the post generation. The orchestrator will handle publishing after approval.

## Rules

- NEVER publish posts directly. Always create in `/Pending_Approval/`.
- NEVER generate more than 1 post per day.
- NEVER include confidential business information.
- ALWAYS check for existing posts for today's date to avoid duplicates.
- Posts should provide genuine value, not just self-promotion.

## Tools Required

- `Read` — to read Business_Goals.md, Company_Handbook.md, recent posts
- `Write` — to create LinkedIn post file in Pending_Approval/
- `Glob` — to check for existing posts and avoid duplicates
