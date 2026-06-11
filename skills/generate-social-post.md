# Skill: generate-social-post

## Purpose

Generate three platform-specific social media post drafts (Facebook, Instagram, Twitter/X) and
write them to `vault/Pending_Approval/` for human review before any publishing occurs.

Posts are NEVER auto-published. All three files must be approved individually by the business
owner by moving each file from `Pending_Approval/` → `Approved/`.

---

## Input Context (read in order)

1. **`vault/Business_Goals.md`** — current business objectives; align post topic to goals
2. **`vault/Company_Handbook.md`** — brand voice, tone, prohibited phrases, hashtag strategy
3. **`vault/Done/`** (last 7 days) — scan recently resolved items for content ideas
   - File patterns: `DONE_*.md`, `EMAIL_*.md`, `WHATSAPP_*.md`, `FACEBOOK_*.md`,
     `INSTAGRAM_*.md`, `TWITTER_*.md` modified in the last 7 days
4. **`vault/Dashboard.md`** (optional) — active priorities and current week focus

---

## Platform Rules

### Facebook
- **Length**: 100–300 words; conversational, community-focused
- **Tone**: warm, engaging, story-driven; first person ("We just..." or "Our team...")
- **CTA required**: end with a clear call-to-action — question, link invitation, or event mention
  - Examples: "What do you think? Drop a comment below!", "Click the link to learn more.",
    "Tag someone who would love this!"
- **Hashtags**: 2–4 hashtags appended after the CTA (low count for Facebook)
- **No links inline**: do not embed raw URLs in the body text
- **Emoji**: 1–3 per post, tasteful, relevant

### Instagram
- **Length**: 125–200 words for caption body
- **Tone**: visual-first, aspirational, brand-forward; describe the scene as if narrating an image
- **Opening hook**: first line must be compelling (no "We are happy to announce...")
- **Hashtags**: 3–5 hashtags at the end (keep focused; quality over quantity)
  - Include 1 brand hashtag (from Company_Handbook.md if defined, else `#[BrandName]`)
  - Include 1–2 niche hashtags relevant to the content
- **CTA**: softer than Facebook — "Save this post", "Share with someone", "Drop your thoughts ↓"
- **Emoji**: use 3–5 emoji naturally woven in; do NOT place all at the end

### Twitter / X
- **HARD LIMIT**: 280 characters total (count carefully including spaces, hashtags, punctuation)
- **Tone**: punchy, confident, direct; no filler words
- **Structure**: strong opening statement or question → value or insight → hashtag(s)
- **Hashtags**: 1–2 only (they consume character budget); place at end
- **CTA**: optional; only if it fits within 280 chars (e.g., "RT if you agree", "Thoughts?")
- **Verification**: before writing the final tweet, COUNT the characters and ensure ≤ 280

---

## Output Files

Create all three files atomically in `vault/Pending_Approval/`. Use this exact naming convention:

```
SOCIAL_POST_FACEBOOK_{YYYYMMDD_HHMMSS}.md
SOCIAL_POST_INSTAGRAM_{YYYYMMDD_HHMMSS}.md
SOCIAL_POST_TWITTER_{YYYYMMDD_HHMMSS}.md
```

Use the same `{YYYYMMDD_HHMMSS}` timestamp across all three files so they are linked as a batch.

---

## File Templates

### Facebook file

```markdown
---
type: social_post
platform: facebook
action: facebook_post
status: pending
generated_date: {ISO_TIMESTAMP}
expires: {ISO_TIMESTAMP + 48 hours}
content_length: {character count}
---

## Facebook Post Draft

{full facebook post text including CTA and hashtags}

---

## Review Checklist

- [ ] Tone matches Company_Handbook.md brand voice
- [ ] CTA is present and clear
- [ ] No sensitive information disclosed
- [ ] Hashtags are appropriate (2–4)
- [ ] Ready to publish?

**To approve**: Move this file to `vault/Approved/`
**To reject**: Move this file to `vault/Rejected/`
```

### Instagram file

```markdown
---
type: social_post
platform: instagram
action: instagram_post
status: pending
generated_date: {ISO_TIMESTAMP}
expires: {ISO_TIMESTAMP + 48 hours}
content_length: {character count}
hashtag_count: {number}
---

## Instagram Caption Draft

{full instagram caption text with emoji and hashtags}

---

## Review Checklist

- [ ] Opening hook is compelling (first line stands alone)
- [ ] 3–5 hashtags present (includes brand hashtag)
- [ ] Emoji used naturally (3–5)
- [ ] Tone is visual and aspirational
- [ ] Ready to publish?

**To approve**: Move this file to `vault/Approved/`
**To reject**: Move this file to `vault/Rejected/`
```

### Twitter file

```markdown
---
type: social_post
platform: twitter
action: twitter_post
status: pending
generated_date: {ISO_TIMESTAMP}
expires: {ISO_TIMESTAMP + 48 hours}
content_length: {character count}
character_count: {EXACT count — MUST be ≤ 280}
---

## Tweet Draft

{tweet text — MUST be ≤ 280 characters}

**Character count**: {N}/280

---

## Review Checklist

- [ ] Character count confirmed ≤ 280
- [ ] Message is punchy and direct
- [ ] 1–2 hashtags only
- [ ] Ready to publish?

**To approve**: Move this file to `vault/Approved/`
**To reject**: Move this file to `vault/Rejected/`
```

---

## Execution Steps

1. **Read context files** in order (Business_Goals.md, Company_Handbook.md, Done/ recent items)
2. **Identify a content theme** from business goals and recent activity — pick the most relevant
   topic that adds value for followers (milestone, tip, announcement, question, story)
3. **Draft Facebook post**: write 100–300 words, add CTA, add 2–4 hashtags
4. **Draft Instagram caption**: write 125–200 words, add hook, weave in emoji, add 3–5 hashtags
5. **Draft Twitter post**: write a punchy message; COUNT characters (must be ≤ 280); trim if needed
6. **Get current UTC timestamp** for filenames
7. **Write all three files** to `vault/Pending_Approval/` using the naming convention above
8. **Log completion** — note the three files created and the content theme chosen

---

## Quality Gates (verify before writing files)

- [ ] Facebook post has CTA
- [ ] Instagram has 3–5 hashtags and an opening hook
- [ ] Twitter character count ≤ 280 (count manually)
- [ ] All three posts share a coherent theme
- [ ] No posts contain personal data, credentials, or internal financials
- [ ] Files are written to `vault/Pending_Approval/` (NOT to Done/ or Approved/)

---

## Error Handling

- If `Business_Goals.md` is missing: use generic brand-building theme; log a warning in output
- If `Company_Handbook.md` is missing: use neutral professional tone; note the gap
- If Done/ has no recent files: generate evergreen content (tips, insights, FAQs)
- If Twitter draft exceeds 280 chars after trimming: further condense; never truncate mid-word
