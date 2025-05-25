# Etapa 1: build
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar dependencias
COPY package*.json ./
COPY . .

# Instalar dependencias
RUN npm install

# Compilar la aplicación
RUN npm run build

# Etapa 2: producción
FROM node:18-alpine AS runner

WORKDIR /app

# Copiar archivos necesarios desde la build
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Puerto de Next.js
EXPOSE 3000

# Comando por defecto
CMD ["npm", "start"]
