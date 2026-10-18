FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=dependencies /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1
RUN addgroup -S appgroup && adduser -S nextjs -G appgroup
COPY --from=builder --chown=nextjs:appgroup /app/.next/standalone ./
COPY --from=builder --chown=nextjs:appgroup /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["sh", "-c", "HOSTNAME=0.0.0.0 exec node server.js"]