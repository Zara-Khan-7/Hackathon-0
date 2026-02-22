---
skill: post_approved_social
description: Post approved social content to the target platform
triggers:
  - EXECUTE_SOCIAL_ or EXECUTE_FACEBOOK_/INSTAGRAM_/TWITTER_ tasks
requires_approval: false (already approved)
---

# Post Approved Social Content

## When to Use
Triggered when an approved social media post returns from the HITL approval pipeline as an EXECUTE_* file. Posts the content to the specified platform.

## Steps
1. Verify the file originated from Approved/ (check approval chain)
2. Determine platform from metadata (`platform` field or filename prefix)
3. Call the appropriate tool on **ai-employee-social** MCP:
   - Facebook → `post_facebook` with `message`
   - Instagram → `post_instagram` with `caption` (and optional `image_path`)
   - Twitter/X → `post_twitter` with `text`
4. Log the post result (post ID, platform, timestamp)
5. Move task to Done/
6. Update Dashboard.md social stats

## Important Rules
- **REQUIRES prior HITL approval** — never post without it
- Verify the content hasn't been modified since approval
- If the MCP call fails, move to Errors/ — do NOT retry social posts automatically
- Log the exact content that was posted for audit trail
- In DRY_RUN mode, log what would be posted without actually posting
