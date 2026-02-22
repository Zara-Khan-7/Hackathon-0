# Skill: Generate Sales Post

## Purpose
Draft a LinkedIn sales/thought-leadership post for review and approval before publishing.

## Trigger
- Invoked by orchestrator when processing SALESPOST_* files.
- Invoked by scheduler for weekly Friday posts.
- Can be triggered manually.

## Steps
1. Read `Company_Handbook.md` for tone and brand guidelines.
2. Determine the post topic from one of:
   - Explicit topic in the task file body
   - Recent completed tasks (summarize wins/learnings)
   - Trending AI/business topics
   - Engagement data from LinkedIn watcher
3. Draft the post following this structure:
   - **Hook** (first line): Attention-grabbing statement or question
   - **Story/Value** (2-3 paragraphs): Share insight, case study, or tip
   - **Call to Action**: Engagement prompt (question, invitation to DM, link)
   - **Hashtags**: 3-5 relevant hashtags
4. Format the post as markdown in a task file.
5. Create approval request in `Pending_Approval/` (posts always require approval).

## Post Template
```markdown
---
type: sales_post
platform: linkedin
status: draft
priority: medium
requires_approval: true
created: [timestamp]
---

# LinkedIn Post Draft

## Hook
[Attention-grabbing first line]

## Body
[2-3 paragraphs of value content]

## Call to Action
[Engagement prompt]

## Hashtags
#AIAutomation #BusinessGrowth #SmallBusiness

## Metadata
- Target audience: [description]
- Estimated reach: [based on recent engagement]
- Suggested posting time: [day/time]
```

## Rules
- Professional, concise tone — matches Company Handbook guidelines.
- Never publish directly — always route through approval.
- Keep posts under 1300 characters (LinkedIn optimal length).
- Include at least one question to drive engagement.
- No hard selling — focus on value and thought leadership.
