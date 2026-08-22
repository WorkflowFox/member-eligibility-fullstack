# Container image for the web service. Per issue #14: package the
# Next.js app into a production image, configured to reach the api
# service via a build-time environment variable.
#
# Multi-stage build, per _docs/outdated/architecture.md §6:
#   1. deps    -- installs all dependencies (including devDependencies)
#                 needed to run `next build`.
#   2. builder -- copies in the source and runs `next build`.
#   3. runner  -- a slimmer runtime image: production dependencies only
#                 (installed fresh via `npm ci --omit=dev`) plus the
#                 compiled `.next` output. No devDependencies and no
#                 source .ts/.tsx files are copied into this stage.

FROM node:22-slim AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js inlines `NEXT_PUBLIC_*` environment variables into the client
# bundle at build time -- setting them at container runtime has no
# effect once the app is built. So the api service's URL is taken as a
# build ARG and exported as an ENV *before* `next build` runs below,
# rather than being read at runtime (see decision on issue #14).
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

# Production-only dependencies, installed fresh in this stage so that
# devDependencies (vitest, typescript, testing-library, etc.) never end
# up in the runtime image.
COPY package.json package-lock.json ./
RUN npm ci --omit=dev

# Only what `next start` needs to serve the already-built app: the
# compiled output and the Next.js config it reads at startup. No
# source TypeScript files (src/, tests/) are copied into this stage.
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.ts ./next.config.ts

EXPOSE 3000

# `next start` reads the PORT env var natively, defaulting to 3000 for
# local runs, and binds to 0.0.0.0 by default (Cloud Run convention).
CMD ["npx", "next", "start"]
