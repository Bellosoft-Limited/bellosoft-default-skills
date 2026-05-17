# Vue 3 + Nuxt 3 Stack Guidelines
> Sources: Vue 3 Official Style Guide (Priority A & B), Pinia Docs, Nuxt 3 Docs
> Stack: Vue 3 Composition API · TypeScript · Pinia · Nuxt 3

---

## Vue 3 — Non-Negotiable Rules (Priority A: Essential)

- Component names must be **multi-word**: `TodoItem` not `Todo`, `UserCard` not `Card`.
- Always define props with at minimum a type. Never bare array syntax (`defineProps(['status'])`).
- Always use `:key` in `v-for`. Key must be a stable unique ID — never the array index.
- Never put `v-if` and `v-for` on the same element. Filter via a computed property first.
- All styles in non-layout components must be scoped: `<style scoped>` or CSS Modules.

---

## Vue 3 — Strongly Recommended Rules (Priority B)

### Component file structure
- One component per file.
- SFC block order: `<script setup>`, `<template>`, `<style>`.
- Use `<script setup lang="ts">` exclusively — never Options API.

### Naming
- Component filenames: PascalCase (`UserProfile.vue`). Consistent throughout the project.
- Base/presentational components use a prefix: `BaseButton`, `AppIcon`, `VTable` — pick one prefix and use it everywhere.
- Child components tightly coupled to a parent include the parent name: `TodoListItem`, `SearchSidebarNavigation`.
- Component names start with the most general word: `SearchButtonClear` not `ClearSearchButton`.
- Full words, no abbreviations: `StudentDashboardSettings` not `SdSettings`.
- Props: camelCase in `defineProps`, kebab-case in templates (SFC can use either — be consistent).

### Templates
- Multi-attribute elements span multiple lines — one attribute per line.
- No complex expressions in templates. Move to computed properties.
- Break complex computed properties into multiple simpler ones.
- Use directive shorthands consistently: either always use `:`, `@`, `#`, or never (mixing is banned).
- Self-close components with no content: `<MyComponent/>` not `<MyComponent></MyComponent>`.
- Always quote attribute values.

---

## TypeScript

- No `any`. Use `unknown` and narrow, or define proper interfaces.
- All component props use typed `defineProps<Props>()` with TypeScript interface.
- All emits use typed `defineEmits<{ ... }>()`.
- Use `interface` for object shapes, `type` for unions and aliases.
- Prefer `readonly` on props interfaces.

---

## Composables

- One composable = one concern.
- Name with `use` prefix: `useOrderStore`, `useAuth`, `useIntersectionObserver`.
- Always call composables at the top level of `setup` — never inside conditions, loops, or event handlers.
- Return plain object of refs/computed — not a `reactive()` object.
- Extract shared logic into composables. Do not duplicate reactive logic across components.

---

## Pinia Stores

- Use **Setup store syntax** (not Options syntax): gives full Composition API power and TypeScript inference.
- Name: `use` + noun + `Store`: `useCartStore`, `useUserStore`.
- One store per domain concept. Do not create a single god store.
- Define state with `ref()`, getters with `computed()`, actions as `function()`.
- Return all state, getters, and actions from the setup function.
- Never mutate store state from outside the store. Use actions.
- Use `storeToRefs()` when destructuring store state to preserve reactivity.
- Never destructure reactive state directly from a store object (breaks reactivity).
- Actions are async when performing I/O. Always use `async/await`.

---

## Nuxt 3

### Auto-imports
- Rely on Nuxt auto-imports for composables, utils, and components — do not manually import things already in `composables/`, `utils/`, or `components/`.
- Use `#imports` only when explicit import is required for clarity or testing.

### Data fetching
- Use `useFetch` or `useAsyncData` for server-side and client-side data fetching — never `fetch()` directly in `setup` (no SSR handling).
- Use `lazy: true` option for non-critical data to avoid blocking page render.
- Handle `pending`, `error`, and `data` states from `useFetch`/`useAsyncData` in templates.
- Use `$fetch` for client-only API calls (user interactions, mutations).

### Pages and routing
- Page files in `pages/` define routes automatically — never manually register routes.
- Use `<NuxtLink>` for all internal navigation — never `<a href>`.
- Use route params and query strings via `useRoute()`, not direct `$route` access.
- Middleware goes in `middleware/` — use named middleware for route guards.

### Server routes (Nitro)
- Server API routes go in `server/api/` — follow RESTful path naming.
- Always validate and sanitize input in server routes — they are public HTTP endpoints.
- Use `defineEventHandler` — never raw Nitro handlers.

### SEO
- Set page metadata with `useSeoMeta` or `useHead` per page — not globally for everything.

### SSR considerations
- Never access `window`, `document`, or `localStorage` at setup time. Guard with `import.meta.client` or use `onMounted`.
- Composables called during SSR must not depend on browser APIs.

---

## Performance

- Use `v-memo` on expensive list items that rarely change.
- Use `<Suspense>` for async components with meaningful loading states.
- Lazy-load route pages: Nuxt does this automatically with `pages/`.
- Avoid large reactive objects — prefer storing IDs and deriving full objects via computed.
- Avoid `watch` with `deep: true` on large objects. Watch specific properties instead.

---

## What to Never Do

- Never use Options API in new code.
- Never use `v-if` + `v-for` on the same element.
- Never use the array index as `:key` in `v-for`.
- Never mutate props directly inside a component. Emit events or use a store.
- Never destructure Pinia store state without `storeToRefs()`.
- Never access browser APIs (`window`, `localStorage`) at the top level of `setup` — they break SSR.
- Never use unscoped styles in non-layout components.
- Never use Options API `this` context in Composition API code.
