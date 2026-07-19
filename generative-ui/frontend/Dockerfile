# gen-UI frontend: build the Vite app, then serve the static bundle via nginx.
FROM node:20-alpine AS build
WORKDIR /app

# The gen-UI backend URL is baked in at build time (Vite embeds import.meta.env).
# It must be host-reachable from the browser, so default to the mapped localhost port.
ARG VITE_API_BASE_URL=http://localhost:8001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY package*.json ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
