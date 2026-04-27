FROM node:20-slim

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY apps/web/package.json ./package.json
COPY pnpm-lock.yaml ./pnpm-lock.yaml
RUN pnpm install --frozen-lockfile || pnpm install

COPY apps/web/. .

EXPOSE 3000

CMD ["pnpm", "dev"]
