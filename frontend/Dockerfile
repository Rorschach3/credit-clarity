# frontend/Dockerfile.flexible
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# More flexible installation approach
RUN npm install --package-lock-only 2>/dev/null || true
RUN npm install --no-audit --no-fund

# Copy source code
COPY . .

# Build the application
RUN npm run build

EXPOSE 8080

CMD ["npm", "start"]