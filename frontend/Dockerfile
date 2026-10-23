FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
# Overridden per environment (Compose service name / Kubernetes Service DNS).
ENV BACKEND_URL=http://backend:8000 \
    NGINX_ENVSUBST_FILTER=BACKEND_URL
EXPOSE 8080
