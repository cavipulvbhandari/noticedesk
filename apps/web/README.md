# NoticeDesk Web

Next.js 14 App Router + Tailwind + shadcn/ui design tokens.

## Local development

```bash
pnpm install   # or npm/yarn at the repo root
cp .env.example .env.local
pnpm dev
```

Open http://localhost:3000.

## Routes

- `/` — public landing page.
- `/login` — Sprint 1 development sign-in form. Stores tenant_id + user_id in
  an httpOnly cookie. The real Clerk/Auth0 flow lands in Sprint 2.
- `/dashboard` — server component that calls the API's `/v1/session` endpoint
  with `X-Dev-User-Id` and `X-Dev-Tenant-Id` headers (development only) and
  renders the logged-in user + tenant.

## Design tokens

Navy / white / slate / gold palette in `tailwind.config.ts`. Don't add
ad-hoc colors in components.
