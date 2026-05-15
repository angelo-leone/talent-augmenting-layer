---
send_after_days: 0
trigger: subscription_cancelled
audience: any user who cancels paid
subject_options:
  - "Cancelled. Your data is yours."
  - "All cancelled. Here's what stays with you."
  - "Subscription cancelled — confirming what happens next"
chosen_subject: ""
---

Hi {{ first_name }},

Confirming: your TAOS subscription is cancelled, effective {{ access_until }}. After that date the coach moves to read-only mode; before then you keep full access.

Three things you might want to do before {{ access_until }}:

1. **Export your profile** at {{ app_url }}/dashboard. The download bundle for Claude, ChatGPT or Gemini is one paste you can keep wherever you keep system prompts.

2. **Export your full data** at {{ app_url }}/account/export. Includes your assessment history, interaction logs, and every profile version.

3. **Delete your account** at {{ app_url }}/account if you want everything wiped, not just paused. Permanent.

If something we did or did not do made you cancel, please tell me. Specific is more useful than polite.

Thanks for trying TAOS.

Angelo
