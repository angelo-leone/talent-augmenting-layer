# Talent-Augmenting Layer — Claude Project Setup

> Set up Talent-Augmenting Layer as a Claude Project for the richest non-MCP experience.

## Requirements
- Claude Pro subscription (for Projects feature)

## Setup Steps

### 1. Create the Project
1. Go to [claude.ai](https://claude.ai)
2. Click **Projects** in the left sidebar
3. Click **+ Create Project**
4. Name it: **Talent-Augmenting Layer**

### 2. Add Project Instructions
1. Click the **⚙️ Settings** icon on your project
2. In **Project Instructions**: paste the FULL contents of `universal-prompt/SYSTEM_PROMPT.md`
3. This becomes the system prompt for every conversation in this project

### 3. Add Your Profile as Knowledge
1. In the project, click **+ Add content** > **Add text**
2. Paste the contents of your `pro-yourname.md` profile
3. Name it: "Talent-Augmenting Layer Profile — [Your Name]"
4. Claude will automatically reference this in every conversation

### 4. First-Time Assessment
If you don't have a profile yet:
1. Start a conversation in the project
2. Say: "Assess me — create my Talent-Augmenting Layer profile"
3. Claude will guide you through the ~15 minute conversational assessment
4. Copy the generated profile and add it as project knowledge (step 3 above)

### 5. Keeping Your Profile Updated
- After substantive work sessions, Claude will output a PROFILE UPDATE BLOCK
- Update the profile in your project knowledge with the new content
- Claude Projects support file versioning — your old profile is preserved

### 6. Why Claude Projects is the Best Non-MCP Option
- **Persistent context**: Profile stays loaded across all conversations in the project
- **Full prompt support**: No character limits on project instructions
- **Knowledge files**: Upload your profile as a separate, manageable file
- **Conversation history**: Track your growth across sessions
- **Artefacts**: Claude can generate visual outputs for coaching exercises

### 7. Optional: Add Assessment Prompt
For running assessments within the project:
1. Add `universal-prompt/ASSESSMENT_PROMPT.md` as another knowledge file
2. When you say "assess me", Claude has the full TALQ instrument available

---

*Talent-Augmenting Layer v0.2.0 — CC BY-NC-SA 4.0*
