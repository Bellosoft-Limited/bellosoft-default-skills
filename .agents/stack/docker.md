# Docker & Container Rules
> Sources: Docker Build Best Practices, Dockerfile Reference
> Stack: Docker · Docker Compose · Multi-stage builds

---

## Dockerfile Structure

- Use multi-stage builds: one stage for building, one (slim) stage for the final image.
- Keep production images minimal — no build tools, compilers, or debuggers in the final stage.
- Name your stages meaningfully: `AS build`, `AS publish`, `AS final`.
- Reusable stages should be at the top, derivative stages reference them with `FROM base AS ...`.

```dockerfile
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app

# Stage 2: Runtime
FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS final
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENTRYPOINT ["dotnet", "MyApp.dll"]
```

---

## Base Image Selection

- Prefer official Docker images (`mcr.microsoft.com/dotnet`, `alpine`, `ubuntu`).
- Use `-slim`, `-alpine`, or `-distroless` variants for production to reduce attack surface.
- Pin base images to a specific tag (e.g., `9.0-alpine`), never use `latest`.
- Optionally pin to a digest for maximum reproducibility (but combine with automation to update).
- For .NET, use `mcr.microsoft.com/dotnet/aspnet:9.0-alpine` for runtime, `mcr.microsoft.com/dotnet/sdk:9.0` for build.

---

## .dockerignore

- Always include a `.dockerignore` to exclude unnecessary files from the build context:

```
**/.classpath
**/.dockerignore
**/.env
**/.git
**/.gitignore
**/.project
**/.settings
**/.toolstarget
**/.vs
**/.vscode
**/*.*proj.user
**/*.dbmdl
**/*.jfm
**/bin
**/charts
**/docker-compose*
**/compose*
**/Dockerfile*
**/node_modules
**/npm-debug.log
**/obj
**/secrets.dev.yaml
**/values.dev.yaml
README.md
```

---

## Dockerfile Instructions — Rules

### FROM
- Always `FROM <image>:<tag>` — never `FROM <image>:latest`.
- Use `--platform=$BUILDPLATFORM` for multi-platform builds.

### RUN
- Combine `apt-get update` and `apt-get install` in the same `RUN` statement to avoid stale cache issues.
- Clean up package cache in the same layer: `rm -rf /var/lib/apt/lists/*`.
- Use `--no-install-recommends` to avoid unnecessary packages.

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
```

- Use `set -o pipefail &&` before pipe chains in `RUN` to catch early failures.
- Sort package lists alphanumerically for maintainability.

### COPY
- Prefer `COPY` over `ADD` for local files. `ADD` has hidden behaviors (tar auto-extraction, remote URL fetching).
- Use `COPY --from=<stage>` to copy artifacts between stages in multi-stage builds.

### EXPOSE
- Document the port your app listens on: `EXPOSE 8080`.
- Use the actual port the app uses (ASP.NET Core defaults to 8080, not 80).

### ENTRYPOINT vs CMD
- Use `ENTRYPOINT` for the main executable: `ENTRYPOINT ["dotnet", "MyApp.dll"]`.
- Use `CMD` to provide default arguments: `CMD ["--environment", "Production"]`.
- Prefer exec form (`["executable", "arg"]`) over shell form (`executable arg`).

### WORKDIR
- Always use absolute paths: `WORKDIR /app`, never `WORKDIR app`.
- Use `WORKDIR` instead of `RUN cd ... && ...`.

### USER
- Run containers as non-root. Create a user in the Dockerfile:

```dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
```

- Do not install or use `sudo` inside containers.

### ENV
- Use `ENV` for runtime configuration: `ENV ASPNETCORE_ENVIRONMENT=Production`.
- Set `ASPNETCORE_URLS=http://+:8080` to bind to the correct port.
- Clear sensitive ENV vars in the same layer they are used to prevent persistence.

### LABEL
- Add labels for organization metadata:

```dockerfile
LABEL org.opencontainers.image.source="https://github.com/org/repo"
LABEL org.opencontainers.image.description="My App"
```

---

## Build Best Practices

- Use `docker build --pull` to get fresh base images.
- Use `docker build --no-cache` for clean builds (or combine: `--pull --no-cache`).
- Leverage Docker layer caching: order Dockerfile instructions from least to most frequently changing:

```
1. FROM (rarely changes)
2. COPY package.json / RUN package install (changes with dependencies)
3. COPY src/ (changes most frequently)
```

- Keep containers **ephemeral** — they can be killed, replaced, and rebuilt with minimum setup.

---

## Docker Compose

- Use Docker Compose for local development and integration tests.
- Always specify version and service names explicitly in `compose.yaml`.
- Use environment variables with `.env` files for configuration — never hardcode secrets.

```yaml
services:
  api:
    build:
      context: .
      target: final
    ports:
      - "8080:8080"
    environment:
      - ASPNETCORE_ENVIRONMENT=Development
      - ConnectionStrings__DefaultConnection=Server=db;Database=app;...
    depends_on:
      - db

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- One concern per container (web app, database, cache — separate services).
- Use `depends_on` for startup ordering.
- Do not use `depends_on` as a health check — use `healthcheck` for that.
- Use named volumes for persistent data, bind mounts for development hot-reload.

---

## Security

- Never run containers as root. Always `USER` directive.
- Never store secrets in Dockerfiles or images. Use Docker secrets, environment variables, or a secrets manager.
- Scan images for vulnerabilities: `docker scout` or `trivy` in CI.
- Use images from trusted sources (Docker Official Images, Verified Publisher).
- Keep images small — fewer packages means fewer vulnerabilities.
- Rebuild images regularly to pick up security patches in base images.

---

## CI Integration

- Build and test Docker images in CI (GitHub Actions or Azure Pipelines).
- Build with `--pull` to get fresh base images.
- Run integration tests against the containerized application.
- Push images to a container registry (ACR, Docker Hub) with a unique tag:

```yaml
- name: Build and push
  uses: docker/build-push-action@<sha>
  with:
    push: true
    tags: myregistry.azurecr.io/myapp:${{ github.sha }}
```

---

## What to Never Do

- Never use `FROM ...:latest` — always pin to a specific tag or digest.
- Never store secrets in the Dockerfile (API keys, passwords, connection strings).
- Never run containers as root in production.
- Never use `ADD` for remote URLs when `COPY` + `curl` + `RUN` in a build stage is clearer.
- Never install `sudo`, compilers, or debug tools in production images.
- Never put `apt-get update` in a separate `RUN` from `apt-get install`.
- Never use shell form (`CMD command args`) for `ENTRYPOINT` or `CMD` — use exec form.
- Never hardcode environment-specific values in Dockerfiles — use build args or env vars.
