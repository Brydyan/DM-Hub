FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

# Servidor de desarrollo de Vite accesible desde el host
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
