# New Engineer Onboarding Guide

Welcome to the Platform Engineering team at Nimbus Data! This guide
covers everything you need during your first two weeks.

## Week 1: Setup and Orientation

### Day 1 — Accounts and Access

- IT will provision your laptop, email, and Slack account before your
  start date.
- Request access to the `platform-eng` GitHub organization from your
  manager.
- Complete the mandatory security awareness training in the LMS portal
  within your first 3 days.

### Day 2-3 — Environment Setup

1. Clone the `nimbus-infra` monorepo.
2. Install the toolchain using the provided `bootstrap.sh` script.
3. Run the local development stack with `make dev-up` and confirm the
   health check endpoint returns `200 OK` at `localhost:8080/health`.
4. Join the `#platform-eng` and `#platform-eng-oncall` Slack channels.

### Day 4-5 — First Contributions

Your onboarding buddy will assign a "good first issue" labeled ticket.
These are intentionally scoped to be completed within a day and touch
a small, well-tested part of the codebase, such as adding a metric or
fixing a documentation typo.

## Week 2: Deeper Integration

### On-call Shadowing

New engineers shadow one on-call rotation before joining the rotation
themselves. Shadowing means you receive pages but are not expected to
resolve them — the primary on-call engineer handles the incident while
you observe.

### Architecture Deep Dives

The team runs three architecture deep-dive sessions during your second
week:

- **Service Mesh Overview** — how traffic is routed between the 40+
  internal services.
- **Data Pipeline Walkthrough** — how event data flows from ingestion
  to the analytics warehouse.
- **Deployment Pipeline** — how a pull request becomes a production
  deployment, including the canary rollout process.

### 30-Day Check-in

At the end of your first month, you and your manager will have a
30-day check-in to review:

- Progress on onboarding tasks
- Any blockers or missing access
- Initial goals for your first quarter

## Key Contacts

| Role | Name | Slack |
|------|------|-------|
| Onboarding Buddy | Assigned individually | @buddy |
| Manager | Your hiring manager | @manager |
| IT Support | Help Desk | #it-support |
| Security Questions | Security Team | #security |

## Frequently Asked Questions

**Q: What if `make dev-up` fails?**
Check `#platform-eng` for a pinned troubleshooting doc; most failures
are due to a stale Docker cache and are fixed by `make dev-clean`.

**Q: When do I get added to the on-call rotation?**
Typically after 6-8 weeks, once you've shadowed at least one full
rotation and your manager confirms readiness.

**Q: Who approves my first pull request?**
Your onboarding buddy is your default reviewer for the first month.
