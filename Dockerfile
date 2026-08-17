FROM node:22-alpine
WORKDIR /app
COPY package.json package-lock.json server.mjs README.md ./
COPY scripts ./scripts
COPY public ./public
COPY data ./data
RUN npm run build:catalog
EXPOSE 8787
CMD ["npm", "start"]
