#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { createClerkClient, verifyToken } from '@clerk/backend';
import { z } from 'zod';

// Clerk client instance
let clerkClient: ReturnType<typeof createClerkClient> | null = null;

// Environment validation schema
const EnvSchema = z.object({
  CLERK_SECRET_KEY: z.string().min(1, 'CLERK_SECRET_KEY is required'),
  CLERK_PUBLISHABLE_KEY: z.string().optional(),
  CLERK_JWT_KEY: z.string().optional(),
  CLERK_DOMAIN: z.string().optional(),
  CLERK_IS_SATELLITE: z.string().transform(val => val === 'true').optional(),
  CLERK_PROXY_URL: z.string().optional(),
  CLERK_API_URL: z.string().optional(),
  CLERK_API_VERSION: z.string().optional(),
});

// Initialize Clerk client
function initializeClerkClient() {
  try {
    const env = EnvSchema.parse(process.env);
    
    clerkClient = createClerkClient({
      secretKey: env.CLERK_SECRET_KEY,
      publishableKey: env.CLERK_PUBLISHABLE_KEY,
      jwtKey: env.CLERK_JWT_KEY,
      domain: env.CLERK_DOMAIN,
      isSatellite: env.CLERK_IS_SATELLITE,
      proxyUrl: env.CLERK_PROXY_URL,
      apiUrl: env.CLERK_API_URL || 'https://api.clerk.com',
      apiVersion: env.CLERK_API_VERSION || 'v1',
      userAgent: 'mcp-clerk-backend/1.0.0',
    });
    
    console.error('✅ Clerk client initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize Clerk client:', error);
    throw error;
  }
}

// Tool definitions
const TOOLS = [
  // Users
  {
    name: 'clerk_get_user',
    description: 'Get a user by ID',
    inputSchema: {
      type: 'object',
      properties: {
        userId: { type: 'string', description: 'The user ID' }
      },
      required: ['userId']
    }
  },
  {
    name: 'clerk_get_user_list',
    description: 'Get a list of users',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Number of users to return (max 500)', default: 10 },
        offset: { type: 'number', description: 'Number of users to skip', default: 0 },
        orderBy: { type: 'string', description: 'Field to order by', default: 'created_at' },
        emailAddress: { type: 'array', items: { type: 'string' }, description: 'Filter by email addresses' },
        phoneNumber: { type: 'array', items: { type: 'string' }, description: 'Filter by phone numbers' },
        username: { type: 'array', items: { type: 'string' }, description: 'Filter by usernames' },
        organizationId: { type: 'array', items: { type: 'string' }, description: 'Filter by organization IDs' },
        query: { type: 'string', description: 'Search query' },
      }
    }
  },
  {
    name: 'clerk_create_user',
    description: 'Create a new user',
    inputSchema: {
      type: 'object',
      properties: {
        emailAddress: { type: 'array', items: { type: 'string' }, description: 'Email addresses' },
        phoneNumber: { type: 'array', items: { type: 'string' }, description: 'Phone numbers' },
        username: { type: 'string', description: 'Username' },
        password: { type: 'string', description: 'Password' },
        firstName: { type: 'string', description: 'First name' },
        lastName: { type: 'string', description: 'Last name' },
        publicMetadata: { type: 'object', description: 'Public metadata' },
        privateMetadata: { type: 'object', description: 'Private metadata' },
        unsafeMetadata: { type: 'object', description: 'Unsafe metadata' },
        skipPasswordChecks: { type: 'boolean', description: 'Skip password validation', default: false },
        skipPasswordRequirement: { type: 'boolean', description: 'Skip password requirement', default: false },
        createdAt: { type: 'string', description: 'Creation date (ISO 8601)' },
      }
    }
  },
  {
    name: 'clerk_update_user',
    description: 'Update a user',
    inputSchema: {
      type: 'object',
      properties: {
        userId: { type: 'string', description: 'The user ID' },
        firstName: { type: 'string', description: 'First name' },
        lastName: { type: 'string', description: 'Last name' },
        primaryEmailAddressId: { type: 'string', description: 'Primary email address ID' },
        primaryPhoneNumberId: { type: 'string', description: 'Primary phone number ID' },
        username: { type: 'string', description: 'Username' },
        profileImageId: { type: 'string', description: 'Profile image ID' },
        password: { type: 'string', description: 'Password' },
        publicMetadata: { type: 'object', description: 'Public metadata' },
        privateMetadata: { type: 'object', description: 'Private metadata' },
        unsafeMetadata: { type: 'object', description: 'Unsafe metadata' },
        skipPasswordChecks: { type: 'boolean', description: 'Skip password validation' },
        signOutOfOtherSessions: { type: 'boolean', description: 'Sign out of other sessions' },
        createdAt: { type: 'string', description: 'Creation date (ISO 8601)' },
      },
      required: ['userId']
    }
  },
  {
    name: 'clerk_delete_user',
    description: 'Delete a user',
    inputSchema: {
      type: 'object',
      properties: {
        userId: { type: 'string', description: 'The user ID' }
      },
      required: ['userId']
    }
  },
  
  // Organizations
  {
    name: 'clerk_get_organization',
    description: 'Get an organization by ID',
    inputSchema: {
      type: 'object',
      properties: {
        organizationId: { type: 'string', description: 'The organization ID' }
      },
      required: ['organizationId']
    }
  },
  {
    name: 'clerk_get_organization_list',
    description: 'Get a list of organizations',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Number of organizations to return (max 500)', default: 10 },
        offset: { type: 'number', description: 'Number of organizations to skip', default: 0 },
        includeMembersCount: { type: 'boolean', description: 'Include members count', default: false },
        query: { type: 'string', description: 'Search query' },
        orderBy: { type: 'string', description: 'Field to order by', default: 'created_at' },
      }
    }
  },
  {
    name: 'clerk_create_organization',
    description: 'Create a new organization',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Organization name' },
        slug: { type: 'string', description: 'Organization slug' },
        createdBy: { type: 'string', description: 'User ID of creator' },
        publicMetadata: { type: 'object', description: 'Public metadata' },
        privateMetadata: { type: 'object', description: 'Private metadata' },
      },
      required: ['name', 'createdBy']
    }
  },
  
  // Sessions
  {
    name: 'clerk_get_session',
    description: 'Get a session by ID',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: { type: 'string', description: 'The session ID' }
      },
      required: ['sessionId']
    }
  },
  {
    name: 'clerk_get_session_list',
    description: 'Get a list of sessions',
    inputSchema: {
      type: 'object',
      properties: {
        clientId: { type: 'string', description: 'Filter by client ID' },
        userId: { type: 'string', description: 'Filter by user ID' },
        status: { type: 'string', enum: ['abandoned', 'active', 'ended', 'expired', 'removed', 'replaced', 'revoked'], description: 'Filter by status' },
        limit: { type: 'number', description: 'Number of sessions to return (max 500)', default: 10 },
        offset: { type: 'number', description: 'Number of sessions to skip', default: 0 },
      }
    }
  },
  {
    name: 'clerk_revoke_session',
    description: 'Revoke a session',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: { type: 'string', description: 'The session ID' }
      },
      required: ['sessionId']
    }
  },
  
  // JWT Verification
  {
    name: 'clerk_verify_jwt',
    description: 'Verify a JWT token',
    inputSchema: {
      type: 'object',
      properties: {
        token: { type: 'string', description: 'The JWT token to verify' },
        audience: { type: 'string', description: 'Expected audience' },
      },
      required: ['token']
    }
  },
  
  // Webhooks
  {
    name: 'clerk_verify_webhook',
    description: 'Verify a webhook signature',
    inputSchema: {
      type: 'object',
      properties: {
        payload: { type: 'string', description: 'The webhook payload' },
        headers: { type: 'object', description: 'The webhook headers' },
        secret: { type: 'string', description: 'The webhook secret' },
      },
      required: ['payload', 'headers', 'secret']
    }
  },
] as const;

// Create and configure the server
const server = new Server({
  name: 'mcp-clerk-backend',
  version: '1.0.0',
  capabilities: {
    tools: {},
  },
});

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS,
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (!clerkClient) {
    throw new McpError(
      ErrorCode.InternalError,
      'Clerk client not initialized. Please check your environment variables.'
    );
  }

  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      // User operations
      case 'clerk_get_user': {
        const { userId } = args as { userId: string };
        const user = await clerkClient.users.getUser(userId);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(user, null, 2),
            },
          ],
        };
      }

      case 'clerk_get_user_list': {
        const params = args as any;
        const users = await clerkClient.users.getUserList(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(users, null, 2),
            },
          ],
        };
      }

      case 'clerk_create_user': {
        const params = args as any;
        const user = await clerkClient.users.createUser(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(user, null, 2),
            },
          ],
        };
      }

      case 'clerk_update_user': {
        const { userId, ...params } = args as any;
        const user = await clerkClient.users.updateUser(userId, params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(user, null, 2),
            },
          ],
        };
      }

      case 'clerk_delete_user': {
        const { userId } = args as { userId: string };
        const deletedUser = await clerkClient.users.deleteUser(userId);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(deletedUser, null, 2),
            },
          ],
        };
      }

      // Organization operations
      case 'clerk_get_organization': {
        const { organizationId } = args as { organizationId: string };
        const organization = await clerkClient.organizations.getOrganization({ organizationId });
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(organization, null, 2),
            },
          ],
        };
      }

      case 'clerk_get_organization_list': {
        const params = args as any;
        const organizations = await clerkClient.organizations.getOrganizationList(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(organizations, null, 2),
            },
          ],
        };
      }

      case 'clerk_create_organization': {
        const params = args as any;
        const organization = await clerkClient.organizations.createOrganization(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(organization, null, 2),
            },
          ],
        };
      }

      // Session operations
      case 'clerk_get_session': {
        const { sessionId } = args as { sessionId: string };
        const session = await clerkClient.sessions.getSession(sessionId);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(session, null, 2),
            },
          ],
        };
      }

      case 'clerk_get_session_list': {
        const params = args as any;
        const sessions = await clerkClient.sessions.getSessionList(params);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(sessions, null, 2),
            },
          ],
        };
      }

      case 'clerk_revoke_session': {
        const { sessionId } = args as { sessionId: string };
        const session = await clerkClient.sessions.revokeSession(sessionId);
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(session, null, 2),
            },
          ],
        };
      }

      // JWT operations
      case 'clerk_verify_jwt': {
        const { token, audience } = args as { token: string; audience?: string };
        try {
          // Use the correct Clerk method for JWT verification
          const payload = await verifyToken(token, {
            secretKey: process.env.CLERK_SECRET_KEY!,
            ...(audience && { audience })
          });
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(payload, null, 2),
              },
            ],
          };
        } catch (error) {
          throw new McpError(ErrorCode.InvalidRequest, `JWT verification failed: ${error}`);
        }
      }

      // Webhook operations  
      case 'clerk_verify_webhook': {
        const { payload, headers, secret } = args as { payload: string; headers: Record<string, string>; secret: string };
        
        try {
          // Import Clerk's webhook verification utility
          const { Webhook } = await import('svix');
          const webhook = new Webhook(secret);
          const evt = webhook.verify(payload, headers);
          
          return {
            content: [
              {
                type: 'text',
                text: JSON.stringify(evt, null, 2),
              },
            ],
          };
        } catch (error) {
          throw new McpError(ErrorCode.InvalidRequest, `Webhook verification failed: ${error}`);
        }
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error) {
    // Handle Clerk API errors
    if (error && typeof error === 'object' && 'errors' in error) {
      throw new McpError(
        ErrorCode.InternalError,
        `Clerk API Error: ${JSON.stringify(error.errors)}`
      );
    }
    
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
});

// Initialize and start the server
async function main() {
  try {
    // Initialize Clerk client
    initializeClerkClient();
    
    // Start the server
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('🚀 MCP Clerk Backend Server started successfully');
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', async () => {
  console.error('🛑 Shutting down MCP Clerk Backend Server...');
  await server.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.error('🛑 Shutting down MCP Clerk Backend Server...');
  await server.close();
  process.exit(0);
});

main().catch((error) => {
  console.error('💥 Unhandled error:', error);
  process.exit(1);
});