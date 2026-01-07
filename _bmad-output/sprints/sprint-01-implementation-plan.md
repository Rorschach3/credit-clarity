---
title: "Sprint 1 Implementation Plan"
sprint: "1"
focus: "Authentication Foundation & Upload Processing"
totalPoints: 21
status: "planned"
startDate: "2025-01-13"
estimatedDuration: "2 weeks"
---

# Sprint 1 Implementation Plan

## Overview

This document outlines the implementation plan for Sprint 1, which focuses on completing the authentication foundation and building the upload processing infrastructure. Based on the codebase assessment, Sprint 1 is estimated at **60-70% complete** with substantial existing infrastructure in place.

## Sprint Overview Table

| Story ID | Story Name | Priority | Points | Status | Dependencies |
|----------|-----------|----------|--------|--------|--------------|
| US-01 | User Registration with Validation | P0 | 5 | In Progress | None |
| US-02 | User Login with Rate Limiting | P0 | 3 | In Progress | US-01 |
| US-03 | JWT Token Management | P0 | 3 | Partial | US-01, US-02 |
| US-04 | User Profile Management | P1 | 3 | Partial | US-01 |
| US-05 | Credit Report Upload | P0 | 5 | Partial | None |
| US-06 | Real-time Processing Status | P1 | 3 | Missing | US-05 |
| US-07 | Background Job Processing | P0 | 3 | Partial | US-05 |
| US-08 | Error Handling Framework | P2 | 2 | Missing | All |

## Week 1: Authentication Foundation

### Goal
Establish robust authentication infrastructure with secure password handling, rate limiting, and audit logging.

### Tasks

#### Task 1.1: Create Backend Auth Routes (US-01, US-02)
**Status:** Missing  
**Points:** 5

Create dedicated `/api/v1/auth/` endpoints for user registration and login.

**File Path:** `src/routes/auth.ts`

```typescript
import { Router, Request, Response } from 'express';
import { AuthController } from '../controllers/auth-controller';
import { rateLimiterMiddleware } from '../middleware/rate-limiter';
import { validateRegistration } from '../validators/auth-validator';
import { container } from '../di/container';

const router = Router();
const authController = container.resolve('authController');

// POST /api/v1/auth/register - User registration
router.post('/register', 
  validateRegistration,
  (req: Request, res: Response) => authController.register(req, res)
);

// POST /api/v1/auth/login - User login with rate limiting
router.post('/login',
  rateLimiterMiddleware,
  (req: Request, res: Response) => authController.login(req, res)
);

// POST /api/v1/auth/logout - User logout
router.post('/logout',
  authController.verifyToken,
  (req: Request, res: Response) => authController.logout(req, res)
);

// POST /api/v1/auth/refresh - Refresh access token
router.post('/refresh',
  authController.refreshToken,
  (req: Request, res: Response) => authController.handleRefresh(req, res)
);

export default router;
```

**Related Files to Create/Modify:**
- [`src/controllers/auth-controller.ts`](src/controllers/auth-controller.ts) - Authentication controller
- [`src/services/auth-service.ts`](src/services/auth-service.ts) - Authentication business logic
- [`src/validators/auth-validator.ts`](src/validators/auth-validator.ts) - Input validation

**Definition of Done:**
- [ ] Register endpoint creates user with hashed password
- [ ] Login endpoint validates credentials and returns JWT tokens
- [ ] Logout endpoint invalidates refresh token
- [ ] Refresh token endpoint issues new access token
- [ ] All endpoints return proper error responses
- [ ] Unit tests cover all auth flows (90% coverage)

---

#### Task 1.2: Add Password Complexity Validation (US-01)
**Status:** Enhancement Needed  
**Points:** 2

Enhance password validation to meet security requirements beyond current 8-character minimum.

**File Path:** `src/utils/password-validator.ts`

```typescript
import { PasswordStrength, ValidationResult } from '../types/auth';

export interface PasswordRequirements {
  minLength: number;
  requireUppercase: boolean;
  requireLowercase: boolean;
  requireNumbers: boolean;
  requireSpecialChars: boolean;
  bannedPatterns: string[];
}

const DEFAULT_REQUIREMENTS: PasswordRequirements = {
  minLength: 8,
  requireUppercase: true,
  requireLowercase: true,
  requireNumbers: true,
  requireSpecialChars: true,
  bannedPatterns: [
    'password', '123456', 'qwerty', 'admin', 'letmein'
  ]
};

export function validatePassword(
  password: string,
  requirements: PasswordRequirements = DEFAULT_REQUIREMENTS
): ValidationResult {
  const errors: string[] = [];
  
  // Check minimum length
  if (password.length < requirements.minLength) {
    errors.push(`Password must be at least ${requirements.minLength} characters`);
  }
  
  // Check uppercase
  if (requirements.requireUppercase && !/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }
  
  // Check lowercase
  if (requirements.requireLowercase && !/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }
  
  // Check numbers
  if (requirements.requireNumbers && !/\d/.test(password)) {
    errors.push('Password must contain at least one number');
  }
  
  // Check special characters
  if (requirements.requireSpecialChars && !/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    errors.push('Password must contain at least one special character');
  }
  
  // Check banned patterns
  const lowerPassword = password.toLowerCase();
  for (const pattern of requirements.bannedPatterns) {
    if (lowerPassword.includes(pattern)) {
      errors.push('Password contains a common pattern that is not allowed');
      break;
    }
  }
  
  // Calculate strength
  const strength = calculatePasswordStrength(password, requirements);
  
  return {
    isValid: errors.length === 0,
    errors,
    strength
  };
}

function calculatePasswordStrength(
  password: string,
  requirements: PasswordRequirements
): PasswordStrength {
  let score = 0;
  
  if (password.length >= requirements.minLength) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) score += 1;
  
  if (score <= 2) return 'weak';
  if (score <= 4) return 'fair';
  if (score <= 5) return 'good';
  return 'strong';
}

export function getPasswordStrengthLabel(strength: PasswordStrength): string {
  const labels: Record<PasswordStrength, string> = {
    weak: 'Weak - Please choose a stronger password',
    fair: 'Fair - Consider adding more complexity',
    good: 'Good - This password meets most requirements',
    strong: 'Strong - Excellent password'
  };
  return labels[strength];
}
```

**Configuration (`.env`):**
```env
# Password Policy
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_MAX_LENGTH=128
```

**Definition of Done:**
- [ ] Password validation rejects weak passwords
- [ ] Strength indicator shows on frontend
- [ ] Banned password list is configurable
- [ ] Unit tests validate all rules

---

#### Task 1.3: Implement Redis Rate Limiting (US-02)
**Status:** Enhancement Needed  
**Points:** 3

Replace in-memory rate limiting with Redis-backed implementation for production use.

**File Path:** `src/middleware/rate-limiter.ts`

```typescript
import { Request, Response, NextFunction } from 'express';
import { RedisClient } from '../services/redis-client';
import { RateLimitConfig, RateLimitResult } from '../types/rate-limit';

export class RedisRateLimiter {
  private redis: RedisClient;
  private defaultConfig: RateLimitConfig = {
    windowMs: 60 * 1000, // 1 minute
    maxRequests: 100,
    keyPrefix: 'ratelimit:',
    blockDuration: 5 * 60 * 1000 // 5 minutes block
  };

  constructor(redisClient: RedisClient) {
    this.redis = redisClient;
  }

  async checkRateLimit(
    key: string,
    config: Partial<RateLimitConfig> = {}
  ): Promise<RateLimitResult> {
    const finalConfig = { ...this.defaultConfig, ...config };
    const prefixedKey = `${finalConfig.keyPrefix}${key}`;
    
    const now = Date.now();
    const windowStart = now - finalConfig.windowMs;

    // Use Redis pipeline for atomic operations
    const pipeline = this.redis.pipeline();
    
    // Remove old entries outside the window
    pipeline.zremrangebyscore(prefixedKey, 0, windowStart);
    
    // Add current request
    pipeline.zadd(prefixedKey, now, `${now}-${Math.random()}`);
    
    // Count requests in window
    pipeline.zcard(prefixedKey);
    
    // Set expiry on the key
    pipeline.expire(prefixedKey, Math.ceil(finalConfig.windowMs / 1000));
    
    const results = await pipeline.exec();
    const requestCount = results?.[2]?.[1] as number || 0;

    const remaining = Math.max(0, finalConfig.maxRequests - requestCount);
    const resetTime = Math.ceil((now + finalConfig.windowMs) / 1000);

    if (requestCount > finalConfig.maxRequests) {
      // Increment block counter
      await this.redis.incr(`${prefixedKey}:blocked`);
      const blockCount = await this.redis.get(`${prefixedKey}:blocked`);
      
      return {
        allowed: false,
        remaining: 0,
        resetTime,
        limit: finalConfig.maxRequests,
        blocked: true,
        retryAfter: finalConfig.blockDuration / 1000,
        blockCount: parseInt(blockCount || '0', 10)
      };
    }

    return {
      allowed: true,
      remaining,
      resetTime,
      limit: finalConfig.maxRequests
    };
  }

  createMiddleware(config: Partial<RateLimitConfig> = {}) {
    return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
      // Use IP address and user ID if available
      const key = req.user?.id || req.ip || 'anonymous';
      
      const result = await this.checkRateLimit(key, config);
      
      // Set rate limit headers
      res.setHeader('X-RateLimit-Limit', result.limit);
      res.setHeader('X-RateLimit-Remaining', result.remaining);
      res.setHeader('X-RateLimit-Reset', result.resetTime);
      
      if (!result.allowed) {
        res.setHeader('Retry-After', result.retryAfter);
        res.status(429).json({
          error: 'Too Many Requests',
          message: 'Rate limit exceeded. Please try again later.',
          retryAfter: result.retryAfter
        });
        return;
      }
      
      next();
    };
  }
}

// Specialized rate limiters for different endpoints
export const authRateLimiter = new RedisRateLimiter(
  container.resolve('redisClient')
).createMiddleware({
  windowMs: 15 * 60 * 1000, // 15 minutes
  maxRequests: 5, // 5 login attempts per 15 minutes
  blockDuration: 30 * 60 * 1000 // 30 minute block
});

export const generalRateLimiter = new RedisRateLimiter(
  container.resolve('redisClient')
).createMiddleware({
  windowMs: 60 * 1000, // 1 minute
  maxRequests: 100
});
```

**Configuration (`.env`):**
```env
# Rate Limiting
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_AUTH_WINDOW_MS=900000
RATE_LIMIT_AUTH_MAX_REQUESTS=5
RATE_LIMIT_BLOCK_DURATION=300000
```

**Definition of Done:**
- [ ] Redis-backed rate limiting with sliding window
- [ ] Configurable limits per endpoint
- [ ] Rate limit headers in responses
- [ ] Block mechanism for repeated violations
- [ ] Integration tests with Redis

---

#### Task 1.4: Add Profile Audit Logging (US-04)
**Status:** Missing  
**Points:** 3

Implement audit logging service for profile updates and security events.

**File Path:** `src/services/audit-log-service.ts`

```typescript
import { PrismaClient, AuditAction, AuditResource } from '@prisma/client';
import { Request } from 'express';

export interface AuditLogEntry {
  userId?: string;
  action: AuditAction;
  resource: AuditResource;
  resourceId?: string;
  previousValue?: Record<string, unknown>;
  newValue?: Record<string, unknown>;
  ipAddress?: string;
  userAgent?: string;
  requestId?: string;
  metadata?: Record<string, unknown>;
}

export interface AuditLogFilter {
  userId?: string;
  action?: AuditAction;
  resource?: AuditResource;
  startDate?: Date;
  endDate?: Date;
  resourceId?: string;
}

export class AuditLogService {
  private prisma: PrismaClient;

  constructor(prismaClient: PrismaClient) {
    this.prisma = prismaClient;
  }

  async log(entry: AuditLogEntry): Promise<void> {
    try {
      await this.prisma.auditLog.create({
        data: {
          userId: entry.userId,
          action: entry.action,
          resource: entry.resource,
          resourceId: entry.resourceId,
          previousValue: entry.previousValue,
          newValue: entry.newValue,
          ipAddress: entry.ipAddress,
          userAgent: entry.userAgent,
          requestId: entry.requestId,
          metadata: entry.metadata
        }
      });
    } catch (error) {
      // Log to fallback system if database fails
      console.error('Audit log write failed:', error);
    }
  }

  async logFromRequest(
    entry: Omit<AuditLogEntry, 'ipAddress' | 'userAgent' | 'requestId'>,
    req: Request
  ): Promise<void> {
    await this.log({
      ...entry,
      ipAddress: req.ip || req.socket.remoteAddress,
      userAgent: req.get('User-Agent'),
      requestId: req.get('X-Request-ID')
    });
  }

  async getAuditLogs(filter: AuditLogFilter): Promise<AuditLogEntry[]> {
    const where: Record<string, unknown> = {};

    if (filter.userId) where.userId = filter.userId;
    if (filter.action) where.action = filter.action;
    if (filter.resource) where.resource = filter.resource;
    if (filter.resourceId) where.resourceId = filter.resourceId;
    
    if (filter.startDate || filter.endDate) {
      where.createdAt = {};
      if (filter.startDate) (where.createdAt as Record<string, Date>).gte = filter.startDate;
      if (filter.endDate) (where.createdAt as Record<string, Date>).lte = filter.endDate;
    }

    const logs = await this.prisma.auditLog.findMany({
      where,
      orderBy: { createdAt: 'desc' },
      take: 1000
    });

    return logs.map(log => ({
      userId: log.userId || undefined,
      action: log.action,
      resource: log.resource,
      resourceId: log.resourceId || undefined,
      previousValue: log.previousValue as Record<string, unknown> | undefined,
      newValue: log.newValue as Record<string, unknown> | undefined,
      ipAddress: log.ipAddress || undefined,
      userAgent: log.userAgent || undefined,
      requestId: log.requestId || undefined,
      metadata: log.metadata as Record<string, unknown> | undefined,
      // Note: createdAt is not in AuditLogEntry type but available
    }));
  }
}

// Prisma schema addition
/*
model AuditLog {
  id            String   @id @default(uuid())
  userId        String?
  action        String
  resource      String
  resourceId    String?
  previousValue Json?
  newValue      Json?
  ipAddress     String?
  userAgent     String?
  requestId     String?
  metadata      Json?
  createdAt     DateTime @default(now())

  @@index([userId])
  @@index([action])
  @@index([resource])
  @@index([createdAt])
}
*/
```

**Definition of Done:**
- [ ] Audit log service records all profile changes
- [ ] Previous and new values stored for comparisons
- [ ] IP address and user agent captured
- [ ] Query endpoint for viewing audit logs (admin)
- [ ] Unit tests for audit service

---

## Week 2: Upload & Processing

### Goal
Implement file upload processing with duplicate detection, virus scanning, and real-time status updates.

### Tasks

#### Task 2.1: Add Duplicate File Detection (US-05)
**Status:** Enhancement Needed  
**Points:** 3

Implement file deduplication using SHA-256 hash comparison.

**File Path:** `src/services/duplicate-detection-service.ts`

```typescript
import * as crypto from 'crypto';
import { Readable } from 'stream';
import { FileRecord } from '@prisma/client';

export interface FileHashResult {
  hash: string;
  algorithm: string;
  fileSize: number;
  chunkSize: number;
}

export interface DuplicateCheckResult {
  isDuplicate: boolean;
  existingFile?: FileRecord;
  hash: string;
}

export class DuplicateDetectionService {
  private chunkSize: number;

  constructor(chunkSize: number = 1024 * 1024) { // 1MB chunks
    this.chunkSize = chunkSize;
  }

  async calculateFileHash(
    stream: Readable,
    onProgress?: (bytesProcessed: number, totalBytes: number) => void
  ): Promise<FileHashResult> {
    const hash = crypto.createHash('sha256');
    let bytesProcessed = 0;
    const fileSize = await this.getStreamSize(stream);

    return new Promise((resolve, reject) => {
      stream.on('data', (chunk: Buffer) => {
        hash.update(chunk);
        bytesProcessed += chunk.length;
        onProgress?.(bytesProcessed, fileSize);
      });

      stream.on('end', () => {
        resolve({
          hash: hash.digest('hex'),
          algorithm: 'sha256',
          fileSize,
          chunkSize: this.chunkSize
        });
      });

      stream.on('error', reject);
    });
  }

  private async getStreamSize(stream: Readable): Promise<number> {
    // For files uploaded to temp location, we can get size from fs.stat
    // This is a simplified version
    let size = 0;
    return new Promise((resolve) => {
      stream.on('data', (chunk: Buffer) => {
        size += chunk.length;
      });
      stream.on('end', () => {
        resolve(size);
      });
    });
  }

  async checkDuplicate(
    fileHash: string,
    userId: string,
    prisma: any
  ): Promise<DuplicateCheckResult> {
    const existingFile = await prisma.fileRecord.findFirst({
      where: {
        fileHash,
        userId
      },
      orderBy: { createdAt: 'desc' }
    });

    if (existingFile) {
      return {
        isDuplicate: true,
        existingFile,
        hash: fileHash
      };
    }

    return {
      isDuplicate: false,
      hash: fileHash
    };
  }

  async getDuplicateFiles(
    fileHash: string,
    prisma: any
  ): Promise<FileRecord[]> {
    return prisma.fileRecord.findMany({
      where: { fileHash },
      orderBy: { createdAt: 'desc' }
    });
  }
}
```

**Definition of Done:**
- [ ] SHA-256 hash calculation for uploaded files
- [ ] Duplicate check against user's previous uploads
- [ ] Progress callback for large file hashing
- [ ] Efficient chunk-based processing
- [ ] Unit tests for hash calculation

---

#### Task 2.2: Integrate Virus Scanning (US-05)
**Status:** Missing  
**Points:** 3

Integrate ClamAV or similar virus scanning for uploaded files.

**File Path:** `src/services/virus-scan-service.ts`

```typescript
import { spawn } from 'child_process';
import * as fs from 'fs';
import { promisify } from 'util';
import path from 'path';

const readFile = promisify(fs.readFile);
const unlinkFile = promisify(fs.unlink);

export interface ScanResult {
  clean: boolean;
  virusName?: string;
  scanTime: number;
  error?: string;
}

export interface VirusScannerConfig {
  clamavHost?: string;
  clamavPort?: number;
  clamdscanPath?: string;
  freshclamPath?: string;
  timeout: number;
}

export class VirusScannerService {
  private config: VirusScannerConfig;
  private useClamavNetwork: boolean;

  constructor(config?: Partial<VirusScannerConfig>) {
    this.config = {
      clamavHost: config?.clamavHost || process.env.CLAMAV_HOST || 'localhost',
      clamavPort: config?.clamavPort || 3310,
      clamdscanPath: config?.clamdscanPath || '/usr/bin/clamdscan',
      freshclamPath: config?.freshclamPath || '/usr/bin/freshclam',
      timeout: config?.timeout || 60000 // 60 seconds
    };
    this.useClamavNetwork = process.env.CLAMAV_USE_NETWORK === 'true';
  }

  async scanFile(filePath: string): Promise<ScanResult> {
    const startTime = Date.now();

    try {
      if (this.useClamavNetwork) {
        return await this.scanWithClamavNetwork(filePath, startTime);
      }
      return await this.scanWithClamdscan(filePath, startTime);
    } catch (error) {
      return {
        clean: false,
        scanTime: Date.now() - startTime,
        error: error instanceof Error ? error.message : 'Unknown scan error'
      };
    }
  }

  private async scanWithClamdscan(filePath: string, startTime: number): Promise<ScanResult> {
    return new Promise((resolve) => {
      const clamdscan = spawn(this.config.clamdscanPath, [filePath], {
        timeout: this.config.timeout
      });

      let stdout = '';
      let stderr = '';

      clamdscan.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      clamdscan.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      clamdscan.on('close', (code) => {
        const scanTime = Date.now() - startTime;

        if (code === 0) {
          // Clean
          resolve({
            clean: true,
            scanTime
          });
        } else if (code === 1) {
          // Virus found
          const virusMatch = stdout.match(/Infected files:\s*1\s*\n(?:.+\n)*(.+)/);
          const virusName = virusMatch ? virusMatch[1].trim() : 'Unknown';
          
          resolve({
            clean: false,
            virusName,
            scanTime
          });
        } else {
          // Error
          resolve({
            clean: false,
            scanTime,
            error: `Scan failed with code ${code}: ${stderr}`
          });
        }
      });

      clamdscan.on('error', (error) => {
        resolve({
          clean: false,
          scanTime: Date.now() - startTime,
          error: error.message
        });
      });
    });
  }

  private async scanWithClamavNetwork(filePath: string, startTime: number): Promise<ScanResult> {
    // Use clamav-connector package for network-based scanning
    const { scanStream } = await import('clamav.js');
    const clamav = require('clamav.js');
    
    const scanner = clamav.createScanner(this.config.clamavPort, this.config.clamavHost);
    
    return new Promise((resolve, reject) => {
      const stream = fs.createReadStream(filePath);
      
      scanner.scan(stream, (err: Error | null, object: { viruses: string[] }) => {
        const scanTime = Date.now() - startTime;
        
        if (err) {
          resolve({
            clean: false,
            scanTime,
            error: err.message
          });
          return;
        }
        
        if (object.viruses && object.viruses.length > 0) {
          resolve({
            clean: false,
            virusName: object.viruses[0],
            scanTime
          });
        } else {
          resolve({
            clean: true,
            scanTime
          });
        }
      });
    });
  }

  async updateDefinitions(): Promise<{ success: boolean; message: string }> {
    return new Promise((resolve) => {
      const freshclam = spawn(this.config.freshclamPath, [], {
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let output = '';

      freshclam.stdout.on('data', (data) => {
        output += data.toString();
      });

      freshclam.stderr.on('data', (data) => {
        output += data.toString();
      });

      freshclam.on('close', (code) => {
        if (code === 0) {
          resolve({
            success: true,
            message: 'Virus definitions updated successfully'
          });
        } else {
          resolve({
            success: false,
            message: `Update failed: ${output}`
          });
        }
      });
    });
  }
}
```

**Configuration (`.env`):**
```env
# Virus Scanning
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
CLAMAV_USE_NETWORK=false
CLAMAV_TIMEOUT=60000
```

**Docker Compose Addition:**
```yaml
services:
  clamav:
    image: clamav/clamav:latest
    ports:
      - "3310:3310"
    volumes:
      - clamav-db:/var/lib/clamav
    environment:
      - CLAMAV_NO_CLAMD=1

volumes:
  clamav-db:
```

**Definition of Done:**
- [ ] Virus scanning on file upload
- [ ] Clean files proceed to processing
- [ ] Infected files are quarantined/deleted
- [ ] Scan results logged
- [ ] Unit tests with EICAR test file

---

#### Task 2.3: Implement Redis Queue Adapter (US-07)
**Status:** Missing  
**Points:** 3

Replace in-memory queue with Redis-backed implementation.

**File Path:** `src/queue/redis-queue-adapter.ts`

```typescript
import { RedisClient } from '../services/redis-client';
import { Job, JobStatus, QueueConfig } from '../types/queue';

export class RedisQueueAdapter {
  private redis: RedisClient;
  private config: QueueConfig;
  private processingSet: string;
  private completedSet: string;
  private deadLetterQueue: string;

  constructor(redisClient: RedisClient, config?: Partial<QueueConfig>) {
    this.redis = redisClient;
    this.config = {
      queueName: config?.queueName || 'credit-processing',
      maxRetries: config?.maxRetries || 3,
      retryDelay: config?.retryDelay || 5000,
      jobTimeout: config?.jobTimeout || 300000, // 5 minutes
      deadLetterEnabled: config?.deadLetterEnabled ?? true
    };
    
    this.processingSet = `${this.config.queueName}:processing`;
    this.completedSet = `${this.config.queueName}:completed`;
    this.deadLetterQueue = `${this.config.queueName}:dead`;
  }

  async enqueue(job: Omit<Job, 'id' | 'status' | 'createdAt' | 'updatedAt'>): Promise<string> {
    const jobId = this.generateJobId();
    const now = Date.now();
    
    const jobData: Job = {
      ...job,
      id: jobId,
      status: 'pending',
      createdAt: now,
      updatedAt: now
    };

    // Store job data
    await this.redis.set(
      `${this.config.queueName}:job:${jobId}`,
      JSON.stringify(jobData),
      'EX', 86400 // 24 hour expiry
    );

    // Add to pending queue (list)
    await this.redis.rpush(`${this.config.queueName}:pending`, jobId);

    return jobId;
  }

  async dequeue(): Promise<Job | null> {
    // Get next job from pending queue
    const jobId = await this.redis.lpop(`${this.config.queueName}:pending`);
    
    if (!jobId) {
      return null;
    }

    const jobData = await this.redis.get(`${this.config.queueName}:job:${jobId}`);
    if (!jobData) {
      return null;
    }

    const job = JSON.parse(jobData) as Job;
    job.status = 'processing';
    job.startedAt = Date.now();
    job.updatedAt = Date.now();

    // Update job data
    await this.redis.set(
      `${this.config.queueName}:job:${jobId}`,
      JSON.stringify(job)
    );

    // Add to processing set with timestamp
    await this.redis.zadd(this.processingSet, Date.now(), jobId);

    return job;
  }

  async complete(jobId: string, result: Record<string, unknown>): Promise<void> {
    const jobData = await this.redis.get(`${this.config.queueName}:job:${jobId}`);
    if (!jobData) {
      throw new Error(`Job ${jobId} not found`);
    }

    const job = JSON.parse(jobData) as Job;
    job.status = 'completed';
    job.result = result;
    job.completedAt = Date.now();
    job.updatedAt = Date.now();

    // Update job data
    await this.redis.set(
      `${this.config.queueName}:job:${jobId}`,
      JSON.stringify(job)
    );

    // Move from processing to completed
    await this.redis.zrem(this.processingSet, jobId);
    await this.redis.zadd(this.completedSet, Date.now(), jobId);

    // Clean up old completed jobs after 24 hours
    await this.redis.expire(`${this.config.queueName}:job:${jobId}`, 86400);
  }

  async fail(jobId: string, error: string, attempt: number): Promise<void> {
    const jobData = await this.redis.get(`${this.config.queueName}:job:${jobId}`);
    if (!jobData) {
      throw new Error(`Job ${jobId} not found`);
    }

    const job = JSON.parse(jobData) as Job;
    
    if (attempt >= this.config.maxRetries) {
      // Move to dead letter queue
      job.status = 'failed';
      job.error = error;
      job.failedAt = Date.now();
      job.updatedAt = Date.now();

      await this.redis.set(
        `${this.config.queueName}:job:${jobId}`,
        JSON.stringify(job)
      );

      await this.redis.rpush(this.deadLetterQueue, jobId);
      await this.redis.zrem(this.processingSet, jobId);
    } else {
      // Retry with delay
      job.status = 'pending';
      job.attempts = attempt + 1;
      job.lastError = error;
      job.updatedAt = Date.now();

      await this.redis.set(
        `${this.config.queueName}:job:${jobId}`,
        JSON.stringify(job)
      );

      // Re-queue after delay
      setTimeout(async () => {
        await this.redis.rpush(`${this.config.queueName}:pending`, jobId);
      }, this.config.retryDelay);

      await this.redis.zrem(this.processingSet, jobId);
    }
  }

  async getJob(jobId: string): Promise<Job | null> {
    const jobData = await this.redis.get(`${this.config.queueName}:job:${jobId}`);
    return jobData ? JSON.parse(jobData) : null;
  }

  async getQueueStats(): Promise<{
    pending: number;
    processing: number;
    completed: number;
    deadLetter: number;
  }> {
    const [pending, processing, completed, deadLetter] = await Promise.all([
      this.redis.llen(`${this.config.queueName}:pending`),
      this.redis.zcard(this.processingSet),
      this.redis.zcard(this.completedSet),
      this.redis.llen(this.deadLetterQueue)
    ]);

    return { pending, processing, completed, deadLetter };
  }

  private generateJobId(): string {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

**Definition of Done:**
- [ ] Redis-backed job queue
- [ ] Reliable job processing with retries
- [ ] Dead letter queue for failed jobs
- [ ] Queue statistics endpoint
- [ ] Integration tests

---

#### Task 2.4: Add WebSocket for Real-time Updates (US-06)
**Status:** Missing  
**Points:** 3

Implement WebSocket server for real-time job status updates.

**File Path:** `src/websocket/websocket-server.ts`

```typescript
import { Server as HttpServer } from 'http';
import { Server, Socket } from 'socket.io';
import { JwtPayload } from 'jsonwebtoken';
import { RedisClient } from '../services/redis-client';

export interface WebSocketConfig {
  corsOrigin: string;
  pingInterval: number;
  pingTimeout: number;
}

export interface JobStatusMessage {
  type: 'job_status';
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  result?: Record<string, unknown>;
  error?: string;
  timestamp: number;
}

export interface SubscribeMessage {
  type: 'subscribe';
  jobIds: string[];
}

export class WebSocketServer {
  private io: Server;
  private redis: RedisClient;
  private config: WebSocketConfig;
  private userSockets: Map<string, Set<string>>; // userId -> socketIds
  private jobSubscriptions: Map<string, Set<string>>; // jobId -> socketIds

  constructor(httpServer: HttpServer, redisClient: RedisClient, config?: Partial<WebSocketConfig>) {
    this.redis = redisClient;
    this.config = {
      corsOrigin: config?.corsOrigin || process.env.WS_CORS_ORIGIN || '*',
      pingInterval: config?.pingInterval || 25000,
      pingTimeout: config?.pingTimeout || 20000
    };
    
    this.userSockets = new Map();
    this.jobSubscriptions = new Map();

    this.io = new Server(httpServer, {
      cors: {
        origin: this.config.corsOrigin,
        methods: ['GET', 'POST']
      },
      pingInterval: this.config.pingInterval,
      pingTimeout: this.config.pingTimeout
    });

    this.setupMiddleware();
    this.setupEventHandlers();
    this.subscribeToJobUpdates();
  }

  private setupMiddleware(): void {
    this.io.use(async (socket, next) => {
      try {
        const token = socket.handshake.auth.token || socket.handshake.query.token;
        
        if (!token) {
          return next(new Error('Authentication required'));
        }

        const userId = await this.verifyToken(token as string);
        if (!userId) {
          return next(new Error('Invalid token'));
        }

        (socket as any).userId = userId;
        next();
      } catch (error) {
        next(new Error('Authentication failed'));
      }
    });
  }

  private setupEventHandlers(): void {
    this.io.on('connection', (socket: Socket) => {
      const userId = (socket as any).userId;
      
      // Track user's sockets
      if (!this.userSockets.has(userId)) {
        this.userSockets.set(userId, new Set());
      }
      this.userSockets.get(userId)!.add(socket.id);

      console.log(`User ${userId} connected with socket ${socket.id}`);

      // Handle subscription to job updates
      socket.on('subscribe', (message: SubscribeMessage) => {
        for (const jobId of message.jobIds) {
          if (!this.jobSubscriptions.has(jobId)) {
            this.jobSubscriptions.set(jobId, new Set());
          }
          this.jobSubscriptions.get(jobId)!.add(socket.id);
        }
        
        socket.emit('subscribed', { jobIds: message.jobIds });
      });

      // Handle unsubscription
      socket.on('unsubscribe', (jobIds: string[]) => {
        for (const jobId of jobIds) {
          const subscribers = this.jobSubscriptions.get(jobId);
          if (subscribers) {
            subscribers.delete(socket.id);
            if (subscribers.size === 0) {
              this.jobSubscriptions.delete(jobId);
            }
          }
        }
      });

      // Handle disconnect
      socket.on('disconnect', () => {
        const userSocketSet = this.userSockets.get(userId);
        if (userSocketSet) {
          userSocketSet.delete(socket.id);
          if (userSocketSet.size === 0) {
            this.userSockets.delete(userId);
          }
        }

        // Clean up job subscriptions
        for (const [jobId, subscribers] of this.jobSubscriptions.entries()) {
          subscribers.delete(socket.id);
          if (subscribers.size === 0) {
            this.jobSubscriptions.delete(jobId);
          }
        }

        console.log(`User ${userId} disconnected socket ${socket.id}`);
      });
    });
  }

  private async subscribeToJobUpdates(): Promise<void> {
    // Subscribe to Redis pub/sub for job updates
    const subscriber = this.redis.duplicate();
    await subscriber.connect();
    
    await subscriber.subscribe('job:updates', (message: string) => {
      const jobMessage: JobStatusMessage = JSON.parse(message);
      this.broadcastJobUpdate(jobMessage);
    });
  }

  broadcastJobUpdate(message: JobStatusMessage): void {
    const subscribers = this.jobSubscriptions.get(message.jobId);
    if (subscribers) {
      for (const socketId of subscribers) {
        this.io.to(socketId).emit('job_status', message);
      }
    }
  }

  // Helper to send job update from queue processor
  async notifyJobUpdate(jobId: string, status: JobStatusMessage['status'], data: Partial<JobStatusMessage>): Promise<void> {
    const message: JobStatusMessage = {
      type: 'job_status',
      jobId,
      status,
      timestamp: Date.now(),
      ...data
    };

    // Publish to Redis for distributed support
    await this.redis.publish('job:updates', JSON.stringify(message));

    // Also broadcast directly
    this.broadcastJobUpdate(message);
  }

  private async verifyToken(token: string): Promise<string | null> {
    // Implement JWT verification
    const jwt = require('jsonwebtoken');
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET) as JwtPayload;
      return decoded.sub || decoded.userId;
    } catch {
      return null;
    }
  }

  async shutdown(): Promise<void> {
    await this.io.close();
  }
}
```

**Frontend Integration Example:**
```typescript
// hooks/useJobStatus.ts
import { useEffect, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface JobStatus {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  message?: string;
}

export function useJobStatus(jobId: string, token: string) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket: Socket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:3001', {
      auth: { token },
      transports: ['websocket']
    });

    socket.on('connect', () => {
      setIsConnected(true);
      socket.emit('subscribe', { jobIds: [jobId] });
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
    });

    socket.on('job_status', (message: JobStatus) => {
      if (message.jobId === jobId) {
        setStatus(message);
      }
    });

    return () => {
      socket.emit('unsubscribe', [jobId]);
      socket.disconnect();
    };
  }, [jobId, token]);

  const retry = useCallback(() => {
    // Implement retry logic
  }, []);

  return { status, isConnected, retry };
}
```

**Definition of Done:**
- [ ] WebSocket server handles real-time connections
- [ ] JWT authentication for WebSocket connections
- [ ] Job status broadcasting to subscribed clients
- [ ] Graceful reconnection handling
- [ ] Frontend hook for consuming updates

---

#### Task 2.5: Create Error Envelope Utility (US-08)
**Status:** Missing  
**Points:** 2

Implement consistent error formatting with request_id tracking.

**File Path:** `src/utils/error-envelope.ts`

```typescript
import { Request, Response, NextFunction } from 'express';

export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  requestId: string;
  timestamp: string;
  path: string;
  method: string;
}

export interface ApiErrorOptions {
  code: string;
  message: string;
  statusCode: number;
  details?: Record<string, unknown>;
  cause?: Error;
}

export class ApiError extends Error {
  public readonly code: string;
  public readonly statusCode: number;
  public readonly details?: Record<string, unknown>;
  public readonly cause?: Error;
  public readonly requestId?: string;

  constructor(options: ApiErrorOptions) {
    super(options.message);
    this.name = 'ApiError';
    this.code = options.code;
    this.statusCode = options.statusCode;
    this.details = options.details;
    this.cause = options.cause;
    
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
  }
}

// Predefined error types
export class BadRequestError extends ApiError {
  constructor(message: string = 'Bad Request', details?: Record<string, unknown>) {
    super({
      code: 'BAD_REQUEST',
      message,
      statusCode: 400,
      details
    });
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message: string = 'Unauthorized', details?: Record<string, unknown>) {
    super({
      code: 'UNAUTHORIZED',
      message,
      statusCode: 401,
      details
    });
  }
}

export class ForbiddenError extends ApiError {
  constructor(message: string = 'Forbidden', details?: Record<string, unknown>) {
    super({
      code: 'FORBIDDEN',
      message,
      statusCode: 403,
      details
    });
  }
}

export class NotFoundError extends ApiError {
  constructor(message: string = 'Resource not found', details?: Record<string, unknown>) {
    super({
      code: 'NOT_FOUND',
      message,
      statusCode: 404,
      details
    });
  }
}

export class ConflictError extends ApiError {
  constructor(message: string = 'Conflict', details?: Record<string, unknown>) {
    super({
      code: 'CONFLICT',
      message,
      statusCode: 409,
      details
    });
  }
}

export class InternalServerError extends ApiError {
  constructor(message: string = 'Internal server error', details?: Record<string, unknown>) {
    super({
      code: 'INTERNAL_SERVER_ERROR',
      message,
      statusCode: 500,
      details
    });
  }
}

// Error envelope factory
export function createErrorEnvelope(
  error: Error | ApiError,
  req: Request
): ErrorEnvelope {
  const requestId = req.get('X-Request-ID') || 'unknown';
  
  let apiError: ApiError;
  if (error instanceof ApiError) {
    apiError = error;
  } else {
    // Wrap unknown errors
    apiError = new InternalServerError('An unexpected error occurred');
    apiError.cause = error;
  }

  return {
    error: {
      code: apiError.code,
      message: apiError.message,
      details: apiError.details
    },
    requestId,
    timestamp: new Date().toISOString(),
    path: req.path,
    method: req.method
  };
}

// Express error handler middleware
export function errorHandlerMiddleware(
  err: Error | ApiError,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  const envelope = createErrorEnvelope(err, req);
  
  // Log error with request ID
  console.error(`[${envelope.requestId}] Error:`, {
    code: envelope.error.code,
    message: envelope.error.message,
    path: envelope.path,
    method: envelope.method,
    stack: err instanceof ApiError ? undefined : err.stack
  });

  // Determine status code
  const statusCode = err instanceof ApiError ? err.statusCode : 500;
  
  res.status(statusCode).json(envelope);
}

// Request ID middleware
export function requestIdMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Generate or use existing request ID
  const requestId = req.get('X-Request-ID') || generateRequestId();
  
  res.setHeader('X-Request-ID', requestId);
  (req as any).requestId = requestId;
  
  next();
}

function generateRequestId(): string {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
```

**Usage Example:**
```typescript
// In controllers
import { BadRequestError, NotFoundError } from '../utils/error-envelope';

export class UserController {
  async getUser(req: Request, res: Response): Promise<void> {
    const userId = req.params.id;
    
    const user = await this.userService.findById(userId);
    if (!user) {
      throw new NotFoundError(`User with ID ${userId} not found`);
    }
    
    res.json({ data: user });
  }
}
```

**Definition of Done:**
- [ ] Consistent error format across all endpoints
- [ ] Request ID tracking for debugging
- [ ] Error codes for client handling
- [ ] Error details for validation errors
- [ ] Proper HTTP status codes

---

## Configuration Requirements

### Environment Variables (`.env`)

```env
# ================================
# Application Configuration
# ================================
NODE_ENV=development
PORT=3000
API_VERSION=v1

# ================================
# Database
# ================================
DATABASE_URL="postgresql://user:password@localhost:5432/credit_clarity"
DATABASE_POOL_SIZE=10

# ================================
# Redis
# ================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_CLUSTER_ENABLED=false

# ================================
# Authentication
# ================================
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRY=15m
JWT_REFRESH_TOKEN_EXPIRY=7d
JWT_ISSUER=credit-clarity

# ================================
# Password Policy
# ================================
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
PASSWORD_MAX_LENGTH=128

# ================================
# Rate Limiting
# ================================
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_AUTH_WINDOW_MS=900000
RATE_LIMIT_AUTH_MAX_REQUESTS=5
RATE_LIMIT_BLOCK_DURATION=300000

# ================================
# File Upload
# ================================
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
ALLOWED_FILE_TYPES=pdf,csv,xls,xlsx
MAX_FILES_PER_USER=50

# ================================
# Virus Scanning
# ================================
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
CLAMAV_USE_NETWORK=false
CLAMAV_TIMEOUT=60000

# ================================
# WebSocket
# ================================
WS_PORT=3001
WS_CORS_ORIGIN=http://localhost:3000
WS_PING_INTERVAL=25000
WS_PING_TIMEOUT=20000

# ================================
# Background Jobs
# ================================
QUEUE_NAME=credit-processing
JOB_TIMEOUT=300000
MAX_RETRIES=3
RETRY_DELAY=5000

# ================================
# Logging
# ================================
LOG_LEVEL=info
LOG_FORMAT=json
REQUEST_LOGGING=true
```

---

## Testing Requirements

### Unit Testing Requirements

| Component | Coverage Target | Key Tests |
|-----------|-----------------|-----------|
| Auth Service | 90% | Registration, login, token refresh, logout |
| Password Validator | 95% | All validation rules, strength calculation |
| Rate Limiter | 90% | Request counting, blocking, window management |
| Audit Log Service | 85% | Logging, querying, filtering |
| Duplicate Detection | 90% | Hash calculation, duplicate checking |
| Virus Scanner | 85% | Clean file, infected file, timeout handling |
| Queue Adapter | 90% | Enqueue, dequeue, complete, fail, retry |
| WebSocket Server | 85% | Connection, subscription, broadcasting |
| Error Envelope | 95% | Error creation, formatting, middleware |

### Integration Testing Requirements

| Scenario | Priority | Description |
|----------|----------|-------------|
| Full auth flow | P0 | Register → Login → Access protected resource → Logout |
| Rate limiting | P1 | Verify limits are enforced per IP/user |
| File upload | P0 | Upload → Duplicate check → Virus scan → Queue processing |
| Job processing | P1 | Enqueue → Process → Complete → WebSocket notification |
| WebSocket realtime | P1 | Subscribe → Job update → Unsubscribe |

### E2E Testing Requirements

| User Story | Test Coverage |
|------------|---------------|
| US-01 (Registration) | Password validation, duplicate email, success flow |
| US-02 (Login) | Wrong password, rate limiting, successful login |
| US-04 (Profile) | Update fields, audit log verification |
| US-05 (Upload) | Valid file, invalid file, duplicate, virus |
| US-06 (Real-time) | Status updates via WebSocket |

---

## Definition of Done

### Code Quality
- [ ] All code follows project style guide
- [ ] No linting errors or warnings
- [ ] TypeScript strict mode passes
- [ ] No TODO comments remaining

### Testing
- [ ] Unit tests achieve specified coverage
- [ ] Integration tests pass for all flows
- [ ] E2E tests cover happy path and error cases
- [ ] All tests pass in CI pipeline

### Documentation
- [ ] API endpoints documented (OpenAPI/Swagger)
- [ ] Environment variables documented
- [ ] README updated with new features
- [ ] inline code comments for complex logic

### Security
- [ ] No high/critical vulnerabilities in dependencies
- [ ] Security review completed
- [ ] Audit logging in place for sensitive operations
- [ ] Rate limiting configured appropriately

### Deployment
- [ ] Docker configuration updated if needed
- [ ] Kubernetes manifests updated if applicable
- [ ] Database migrations tested
- [ ] Configuration validated in staging environment

---

## Dependencies Between Tasks

```
Week 1:
├── Task 1.1: Auth Routes (US-01, US-02)
│   ├── Task 1.2: Password Validation (depends on 1.1)
│   └── Task 1.3: Rate Limiting (depends on 1.1)
│   └── Task 1.4: Audit Logging (depends on 1.1)
│
Week 2:
├── Task 2.1: Duplicate Detection (US-05)
│   └── Task 2.2: Virus Scanning (depends on 2.1)
│   └── Task 2.3: Redis Queue (independent)
│   └── Task 2.4: WebSocket (depends on 2.3)
│   └── Task 2.5: Error Envelope (independent)
```

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| ClamAV integration complexity | High | Medium | Use official Docker image, network scanning fallback |
| WebSocket connection stability | Medium | Low | Implement reconnection logic, heartbeat |
| Redis queue reliability | High | Low | Add dead letter queue, comprehensive logging |
| Rate limiting false positives | Medium | Low | Whitelist capability, user-friendly messages |

## Next Steps

1. **Sprint Planning Meeting** - Review this plan with the team
2. **Task Assignment** - Assign owners to each task
3. **Environment Setup** - Ensure Redis and ClamAV are available
4. **Sprint Kickoff** - Begin Week 1 implementation

---

**Document Version:** 1.0  
**Created:** 2025-01-07  
**Last Updated:** 2025-01-07
