FROM node:24-bookworm-slim

WORKDIR /app
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json tsconfig.base.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/ui/package.json packages/ui/package.json
COPY packages/db-types/package.json packages/db-types/package.json

RUN pnpm install --frozen-lockfile

COPY apps/web apps/web
COPY packages/ui packages/ui
COPY packages/db-types packages/db-types

EXPOSE 3000
CMD ["sh", "-c", "pnpm --filter @limitboard/web build && pnpm --filter @limitboard/web exec next start -p ${PORT:-3000}"]
