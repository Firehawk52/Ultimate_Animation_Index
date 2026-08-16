FROM node:22-alpine
RUN apk add --no-cache python3
WORKDIR /app
COPY package.json package-lock.json server.mjs build_catalog.py README.md ./
COPY scripts ./scripts
COPY public ./public
COPY data ./data
RUN npm run build:catalog
EXPOSE 8787
CMD ["npm", "start"]
