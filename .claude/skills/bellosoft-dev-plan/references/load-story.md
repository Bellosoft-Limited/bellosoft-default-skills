# Load the story

Pick the first input type that matches.

## A) Jira ticket ID or URL
- ID pattern: `[A-Z]+-\d+` (`AP-29`, `PROJ-123`).
- URL: find the first `[A-Z]+-\d+` match (`?selectedIssue=AP-29`, `/browse/AP-29`).
- Run `/bellosoft-jira get [issue_key]`.
- Do not show a "no connection" error. The jira skill handles MCP and REST fallback.
- If the jira skill fails, ask the dev to paste the story.

## B) Local .md file
Read the file. If missing, stop and ask for the correct path.

## C) No argument
1. Find the newest `.md` under `docs/stories/`, `stories/`.
2. If found, ask: `Use stories/E1-S2-auth-login.md? (yes/no)`
3. If not found, ask for a ticket ID, file path or pasted story.

## D) Pasted content
Use it as given.

## E) Free-form text
Short phrase, not an ID or path.

1. Use it as title and goal.
2. Ask for ACs:

```
Planning: "add password reset to login"
Need at least one AC. Type them, or reply "draft" and I propose some.
```

3. On "draft", propose ACs and ask the dev to confirm.
4. If `tracker: jira` in `docs/planning-artifacts/status.md`, ask:

```
Create a Jira story first? (yes / no)
```

On yes, run `/bellosoft-jira create-story` with title, goal, confirmed ACs. Use the returned ID as the story source.
If `tracker: none` or no status file, skip the question.
