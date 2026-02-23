---
skill: generate_social_post
description: Create platform-specific social media content for FB/IG/X
triggers:
  - SOCIAL_post tasks
  - FACEBOOK_, INSTAGRAM_, TWITTER_ content tasks
requires_approval: true
---

# Generate Social Post

## When to Use
Triggered when a social media post needs to be drafted for Facebook, Instagram, or Twitter/X. Creates platform-appropriate content and routes to Pending_Approval/.

## Steps
1. Read Company_Handbook.md for brand tone and guidelines
2. Determine target platform from task metadata (`platform` field)
3. Draft content matching platform norms:
   - **Facebook**: Longer form, conversational, can include links, 1-3 paragraphs
   - **Instagram**: Caption-focused, emoji-friendly, hashtag-rich, visual storytelling
   - **Twitter/X**: Under 280 characters, punchy, 2-3 hashtags max, thread-friendly
4. Call `draft_social_post` on **ai-employee-social** MCP with platform and content
5. Create APPROVE_SOCIAL_*.md in Pending_Approval/ with:
   - Platform name
   - Full post content
   - Character count
   - Suggested posting time
6. Log action

## Platform Guidelines
| Platform | Max Length | Tone | Hashtags |
|----------|-----------|------|----------|
| Facebook | ~2000 chars | Professional, conversational | 2-3 |
| Instagram | ~2200 chars | Visual, engaging, emoji-ok | 5-15 |
| Twitter/X | 280 chars | Punchy, concise | 2-3 |

## Important Rules
- **ALL social posts require HITL approval** — never publish directly
- Focus on value, not selling
- Include at least one question or call-to-action
- Match the brand voice from Company_Handbook.md
- If no platform specified, draft for all three platforms
