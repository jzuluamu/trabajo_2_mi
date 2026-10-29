# syntax=docker/dockerfile:1
# Etapas: base -> deps (todas) -> test | build -> runtime (solo dependencias del BFF)
FROM node:24.19.0-alpine3.24 AS base
ENV NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false
RUN addgroup -S app && adduser -S -G app -h /app app
WORKDIR /app
RUN chown app:app /app
USER app

FROM base AS deps
COPY --chown=app:app package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit

FROM deps AS test
COPY --chown=app:app . .
CMD ["sh", "scripts/check.sh"]

FROM deps AS build
COPY --chown=app:app . .
RUN npm run build

FROM base AS runtime
ENV NODE_ENV=production
COPY --chown=app:app package.json package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit && npm cache clean --force
COPY --from=build /app/dist ./dist
EXPOSE 8080
CMD ["node", "dist/server/index.js"]
