# Coding Standards
> Sources: Microsoft C# Conventions, .NET Framework Design Guidelines, Vue 3 Official Style Guide, Google Engineering Practices
> Stack: .NET 9/10 · C# · Vue 3 Composition API · Nuxt 3 · TypeScript · Python

---

## General Principles

- Write code for the next reader, not the compiler.
- Prefer clarity over cleverness. Simple is better than smart.
- One responsibility per class, method, and function.
- If you need a comment to explain what code does, rewrite the code first.
- Never leave commented-out code in the codebase. Use git history.
- Fix warnings. Treat them as errors.

---

## Naming

### Universal rules
- Names must reveal intent. `userList` not `ul`, `isActive` not `flag`.
- Avoid abbreviations except universally accepted ones (`id`, `url`, `dto`, `ctx`).
- Boolean names start with a verb: `isLoading`, `hasError`, `canSubmit`.
- Avoid negative names: `isEnabled` not `isNotDisabled`.
- Don't encode type in names: `customerList` not `listCustomers`, `name` not `nameString`.

### C# naming
| Element | Convention | Example |
|---|---|---|
| Namespace | PascalCase | `Bellosoft.Api.Orders` |
| Class / Struct / Record | PascalCase | `OrderService` |
| Interface | `I` prefix + PascalCase | `IOrderRepository` |
| Public method | PascalCase | `GetOrderById` |
| Private method | PascalCase | `ValidatePayload` |
| Public property | PascalCase | `CreatedAt` |
| Private field | `_` prefix + camelCase | `_orderRepository` |
| Local variable | camelCase | `orderId` |
| Parameter | camelCase | `customerId` |
| Async method | `Async` suffix | `GetOrderByIdAsync` |
| Constant | PascalCase | `MaxRetryCount` |
| Enum type | PascalCase (singular) | `OrderStatus` |
| Enum member | PascalCase | `OrderStatus.Pending` |

### TypeScript / Vue naming
| Element | Convention | Example |
|---|---|---|
| Component file | PascalCase | `OrderSummary.vue` |
| Component name | Multi-word PascalCase | `TodoItem`, `UserProfile` |
| Composable | `use` prefix + camelCase | `useOrderStore`, `useAuth` |
| Emitted event | kebab-case | `update:modelValue`, `item-selected` |
| Prop | camelCase (define) / kebab-case (template) | `userId` / `:user-id` |
| Store (Pinia) | `use` + noun + `Store` | `useCartStore` |
| Route name | kebab-case | `order-detail` |

---

## C# Language Rules

### Variables and types
- Use `var` only when the type is obvious from the right-hand side: `var order = new Order()` ✅ — `var result = GetResult()` ❌
- Use explicit types in `foreach` loops. Never `var` there.
- Use `int` not `Int32`. Use language keywords, not CLR type names.
- Use `required` properties instead of constructor-forced initialization where possible.
- Use collection expressions: `string[] items = ["a", "b"]` not `new string[] { "a", "b" }`.

### Strings
- Use string interpolation for short strings: `$"{first} {last}"`.
- Use `StringBuilder` for string concatenation in loops.
- Use raw string literals (`"""`) for multi-line strings.
- Never use `string.Format` with positional args. Use interpolation.

### Namespaces and usings
- Use file-scoped namespace declarations: `namespace Bellosoft.Orders;`
- Place all `using` directives **outside** the namespace declaration.

### Async/await
- All I/O methods must be async. Never block on async code (no `.Result`, no `.Wait()`).
- Always `await` — never fire-and-forget unless explicitly documented.
- Add `ConfigureAwait(false)` in library code. Not needed in ASP.NET Core controller code.
- Name async methods with `Async` suffix: `GetOrderAsync`.
- Return `Task` not `void` from async methods, except event handlers.
- Use `CancellationToken` parameters on all public async methods.

### Exception handling
- Catch specific exceptions, never `catch (Exception e)` without a filter or rethrow.
- Use `using` declarations, not `try/finally` with `Dispose()`.
- Never swallow exceptions silently.
- Rethrow with `throw;` not `throw ex;` (preserves stack trace).

### LINQ
- Use method syntax for chained operations, query syntax for joins.
- Filter early: place `Where` before other clauses.
- Use meaningful range variable names: `from order in orders` not `from o in o2`.

### Collections
- Return `IEnumerable<T>` or `IReadOnlyList<T>` from public APIs, not `List<T>`.
- Never return `null` from a method that returns a collection. Return empty.

### Null handling
- Enable nullable reference types (`<Nullable>enable</Nullable>`).
- Use null-conditional `?.` and null-coalescing `??` operators.
- Use `ArgumentNullException.ThrowIfNull(param)` at method boundaries.

### Static members
- Call static members with the class name: `ClassName.Member`, never via an instance.
- Never qualify inherited static members with the derived class name.

### Layout
- One statement per line. One declaration per line.
- 4-space indentation. No tab characters.
- Allman brace style: opening and closing braces on their own lines.
- Blank line between method and property definitions.
- XML doc comments (`///`) on all public members.
- Single-line comments (`//`) only. Avoid block comments.
- Comment on a separate line above the code. Uppercase first letter. End with period.

---

## Vue 3 + TypeScript Rules

### Component rules (Priority A — non-negotiable)
- Component names must be multi-word: `TodoItem` not `Todo`, `UserCard` not `Card`.
- Always use `:key` in `v-for`. Key must be a stable unique ID, never the array index.
- Never put `v-if` and `v-for` on the same element. Filter via computed property.
- All styles in non-layout components must be scoped (`<style scoped>`) or use CSS Modules.
- Always define props with type and `required`: never `defineProps(['status'])`.

### Component rules (Priority B — strongly recommended)
- Single-file component files order: `<script>`, `<template>`, `<style>`.
- Use `<script setup lang="ts">` — never Options API.
- Prop definitions use `defineProps<Props>()` with TypeScript interface.
- Emits use `defineEmits<{...}>()` typed form.
- Computed properties, not methods, for values derived from reactive state.
- Complex template expressions belong in computed properties, not inline.

### Composables
- One composable = one concern.
- Always call composables at the top level of `setup`, never inside conditions or loops.
- Composables return a plain object of refs/computed, not reactive objects.

### State (Pinia)
- One store per domain concept.
- Store state is typed with TypeScript interfaces.
- Never mutate state outside of store actions.
- Actions are async when performing I/O.

### TypeScript rules
- No `any`. Use `unknown` and narrow, or define proper types.
- All function parameters and return types must be explicitly typed in non-trivial functions.
- Use `interface` for object shapes (extensible), `type` for unions and aliases.
- Prefer `readonly` arrays and properties in interfaces where mutation is not intended.

---

## Python Rules

- Follow PEP 8. Use `black` for formatting (non-negotiable, configured in CI).
- Use type hints on all function signatures.
- Prefer `pathlib.Path` over `os.path`.
- Use `logging` module, never `print` in production code.
- Functions do one thing. Max 20 lines is a soft limit — question anything longer.
- Use dataclasses or Pydantic models for structured data, not plain dicts.
- Raise specific exceptions, never bare `raise Exception("message")`.

---

## What to Never Do

- Never commit secrets, connection strings, or API keys. Use environment variables or Azure Key Vault.
- Never concatenate SQL strings. Use parameterized queries or ORM.
- Never silence exceptions with empty `catch` blocks.
- Never use `SELECT *` in production queries.
- Never disable compiler warnings with `#pragma warning disable` without a documented reason inline.
- Never return `null` where an empty collection is valid.
- Never use `Thread.Sleep` or `Task.Delay` in production paths.
- Never share mutable state across threads without synchronization.
