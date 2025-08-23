FROM node:20-alpine

# Install system dependencies
RUN apk add --no-cache git wget

WORKDIR /app

# Configure npm for better performance using ENV variables
ENV NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_FETCH_RETRIES=5 \
    NPM_CONFIG_REGISTRY=https://registry.npmjs.org/ \
    NPM_CONFIG_TIMEOUT=300000 \
    NPM_CONFIG_PROGRESS=false

# Copy package files
COPY package*.json ./

# Test npm connectivity and install dependencies with retry logic
RUN for i in 1 2 3; do npm ping && break || sleep 5; done && \
    npm ci --only=production

# Copy source and build files
COPY . .

# Build TypeScript if build script exists
RUN npm run build 2>/dev/null || echo "No build script found, skipping..."

# Create directory for codebase mount point
RUN mkdir -p /workspace && \
    mkdir -p /mnt/c/projects/credit-clarity

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S mcp -u 1001

# Change ownership of app directory and mount points
RUN chown -R mcp:nodejs /app && \
    chown -R mcp:nodejs /workspace && \
    chown -R mcp:nodejs /mnt/c/projects/credit-clarity

# Switch to non-root user
USER mcp

# Set default codebase root (can be overridden via environment variable)
ENV CODEBASE_ROOT=/workspace

# Expose port 3100 to match docker-compose
EXPOSE 3100

# Health check (adjust endpoint as needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider --timeout=5 http://localhost:3100/health || exit 1

# Start the server
CMD ["npm", "start"]