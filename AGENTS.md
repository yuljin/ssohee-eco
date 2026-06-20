# AGENTS.md

## Communication

- Respond in Korean by default.
- Keep progress updates concise and practical.
- Prefer direct execution over long proposals when the requested task is clear.

## Command Policy

- Do not ask for confirmation before routine project commands such as `curl`, `git status`, `git diff`, `git log`, `npm run build`, tests, `vercel list`, `vercel inspect`, or read-only API checks.
- Do not ask for confirmation before `git push` or Vercel deployment checks when the user has asked to deploy or verify the current project.
- Ask before destructive operations such as deleting data, resetting git history, removing services, rotating secrets unexpectedly, or changing billing/security-sensitive settings.

## Project Notes

- Production URL: `https://ssohee-eco.vercel.app`
- Basic Auth user: `yuljin`
- This app uses Vercel for hosting and Neon Postgres for production data.
- Prefer keeping deployment-related changes committed to `main` so GitHub integration triggers Vercel production builds.

## Verification

- For frontend changes, run `npm run build`.
- For backend changes, run `PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests`.
- After deployment, verify production with authenticated `curl` checks when relevant.
