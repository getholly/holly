FROM node:23-slim AS builder
WORKDIR /app

# Copy package files and API tarball
COPY package*.json ./
COPY gen/openapi/holly-api-*.tgz ./gen/openapi/

# Install dependencies
RUN npm ci --ignore-scripts

# Copy application source
COPY . .

# Build the application
RUN npm run build:svelte

FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

