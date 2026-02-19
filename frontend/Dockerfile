FROM node:20-alpine

WORKDIR /app

# Copiar package files primeiro (cache)
COPY package.json package-lock.json ./
RUN npm ci

# Copiar código
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
