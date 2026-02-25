FROM node:20-alpine

WORKDIR /app

# Copiar package files primeiro (cache)
COPY package.json package-lock.json ./
RUN NODE_ENV=development npm install

# Copiar código
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
