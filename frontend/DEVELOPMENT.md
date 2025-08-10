# Frontend stack and conventions

This Angular 20 app uses PrimeNG for UI components and Tailwind CSS v4 for utility-first styling.

## Stack

- Angular 20 standalone APIs (no NgModules)
- Router + Signals
- PrimeNG 20 with `@primeuix/themes` (Aura preset)
- Tailwind CSS 4 with `tailwindcss-primeui` plugin
- PostCSS via `@tailwindcss/postcss`

## Project structure

```
src/
  app/
    app.ts            # Root standalone component
    app.html          # App shell with toolbar and <router-outlet>
    app.css           # App-level styles
    app.config.ts     # Router, animations, PrimeNG theme providers
    app.routes.ts     # Route table
    features/
      welcome/
        welcome.component.ts
        welcome.component.html
    button-demo.*     # Example PrimeNG button page at /demo
  styles.css          # Global styles (Tailwind + PrimeUI plugin)
```

### Naming

- Use `features/<feature-name>/<feature>.component.ts` for routed pages (standalone components).
- Prefer co-located `.html` templates and optional `.css` or `.scss` per component.

## Routing

- Home (`/`) -> `WelcomeComponent`
- Demo (`/demo`) -> `ButtonDemo`

Add a new page:

1. Create a standalone component under `src/app/features/<name>/<name>.component.ts`.
2. Export it and add a route in `app.routes.ts`.

## Tailwind + PrimeNG

- Global CSS (`src/styles.css`):
  - `@import "tailwindcss";`
  - `@plugin "tailwindcss-primeui";`
- Utility classes can be used directly in templates.
- Use PrimeNG components for common UI (Button, Card, Toolbar, Table, Dialog, etc.).

## PrimeNG theme

Configured in `app.config.ts`:

```ts
providePrimeNG({
  theme: { preset: Aura },
});
```

You can switch to another preset from `@primeuix/themes` if needed.

## Coding conventions

- Standalone components only; avoid NgModules.
- Keep components focused; extract small presentational components when templates grow.
- Use `signals` for simple local state and `@Input()`/`@Output()` for composition. Add a state service if shared.

## Tooling

- Angular CLI for serve/build/test.
- Prettier for HTML formatting (configured in `package.json`).

## Quick start

- Dev: `npm start` or `ng serve` (http://localhost:4200)
- Build: `npm run build`

## Notes

- Assets can go under `public/` and are copied to the root of the deployed app.
- Ensure any external links use `rel="noreferrer"` when `target="_blank"`.
