FROM node:20.19.4-alpine

WORKDIR /app

# Copiar package files primeiro (cache)
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Copiar código
COPY . .

EXPOSE 3001

CMD ["npm", "run", "dev"]
