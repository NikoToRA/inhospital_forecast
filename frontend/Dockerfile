# ---------- Build stage ----------
FROM node:18-alpine AS build
WORKDIR /app

# Install deps with clean, reproducible ci
COPY frontend/package*.json ./
# Use npm install to avoid lockfile mismatch failures in CI
RUN npm install --prefer-offline --no-audit --no-fund

# Copy sources
COPY frontend/ ./

# Build-time API base URL (React reads env at build time)
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Build
RUN npm run build

# ---------- Runtime stage (static) ----------
FROM nginx:1.27-alpine

# Remove default conf and add ours (serves SPA and optional proxy rules)
RUN rm -f /etc/nginx/conf.d/default.conf
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Static assets
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
