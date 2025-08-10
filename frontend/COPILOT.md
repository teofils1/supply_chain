# Copilot guide for this frontend

Tech stack

- Angular 20 (standalone components, no NgModules)
- PrimeNG 20 UI with `@primeuix/themes` Aura preset
- Tailwind CSS v4 with `tailwindcss-primeui`

Key files

- `src/app/app.routes.ts` — add routes here
- `src/app/app.config.ts` — DI providers, PrimeNG theme
- `src/styles.css` — Tailwind + PrimeUI plugin
- `src/app/features/*` — routed pages live here
- `src/app/core` — singletons/services
- `src/app/shared` — reusable presentational components

Conventions

- Create pages as standalone components under `src/app/features/<name>/<name>.component.ts` with co-located `.html`.
- Import needed PrimeNG modules at component level (e.g., `ButtonModule`, `CardModule`, `RippleModule`).
- Use Tailwind utility classes in templates.
- Update `app.routes.ts` to register new pages; keep a wildcard redirect to home.

Examples

- "Add a Products page under features/products with a PrimeNG Table showing id, name, status; route at /products; link it from the toolbar."
- "Create a shared Badge component that accepts `text` and `severity` inputs and uses PrimeNG style tokens; add unit tests."
- "Add an HTTP service in core to fetch products from /api/products using fetch with typed response and error handling."

Commands

- Dev: `npm start`
- Build: `npm run build`
- Test: `npm test`
