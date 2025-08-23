# MCP Clerk Backend Usage Examples

## Getting Started

1. Build the project:
```bash
npm run build
```

2. Set up your environment variables:
```bash
cp .env.example .env
# Edit .env with your Clerk credentials
```

3. Test the server locally:
```bash
npm run dev
```

## Tool Examples

### User Management

#### Get User List
```json
{
  "name": "clerk_get_user_list",
  "arguments": {
    "limit": 10,
    "offset": 0,
    "orderBy": "created_at"
  }
}
```

#### Get Specific User
```json
{
  "name": "clerk_get_user",
  "arguments": {
    "userId": "user_2abc123def456"
  }
}
```

#### Create New User
```json
{
  "name": "clerk_create_user",
  "arguments": {
    "emailAddress": ["john.doe@example.com"],
    "firstName": "John",
    "lastName": "Doe",
    "password": "SecurePassword123!",
    "publicMetadata": {
      "role": "user",
      "plan": "basic"
    }
  }
}
```

#### Update User
```json
{
  "name": "clerk_update_user",
  "arguments": {
    "userId": "user_2abc123def456",
    "firstName": "Johnny",
    "publicMetadata": {
      "role": "premium_user"
    }
  }
}
```

#### Delete User
```json
{
  "name": "clerk_delete_user",
  "arguments": {
    "userId": "user_2abc123def456"
  }
}
```

### Organization Management

#### Get Organization List
```json
{
  "name": "clerk_get_organization_list",
  "arguments": {
    "limit": 25,
    "includeMembersCount": true
  }
}
```

#### Get Specific Organization
```json
{
  "name": "clerk_get_organization",
  "arguments": {
    "organizationId": "org_2abc123def456"
  }
}
```

#### Create Organization
```json
{
  "name": "clerk_create_organization",
  "arguments": {
    "name": "Acme Corporation",
    "slug": "acme-corp",
    "createdBy": "user_2abc123def456",
    "publicMetadata": {
      "industry": "technology",
      "size": "startup"
    }
  }
}
```

### Session Management

#### Get Session List
```json
{
  "name": "clerk_get_session_list",
  "arguments": {
    "userId": "user_2abc123def456",
    "status": "active",
    "limit": 10
  }
}
```

#### Get Specific Session
```json
{
  "name": "clerk_get_session",
  "arguments": {
    "sessionId": "sess_2abc123def456"
  }
}
```

#### Revoke Session
```json
{
  "name": "clerk_revoke_session",
  "arguments": {
    "sessionId": "sess_2abc123def456"
  }
}
```

### Authentication & Security

#### Verify JWT Token
```json
{
  "name": "clerk_verify_jwt",
  "arguments": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "audience": "https://your-app.com"
  }
}
```

#### Verify Webhook
```json
{
  "name": "clerk_verify_webhook",
  "arguments": {
    "payload": "{\"type\":\"user.created\",\"data\":{...}}",
    "headers": {
      "svix-id": "msg_abc123",
      "svix-signature": "v1,signature_here",
      "svix-timestamp": "1640995200"
    },
    "secret": "whsec_abc123def456"
  }
}
```

## Advanced Filtering Examples

### Search Users by Email
```json
{
  "name": "clerk_get_user_list",
  "arguments": {
    "emailAddress": ["john@example.com", "jane@example.com"],
    "limit": 50
  }
}
```

### Search Users by Organization
```json
{
  "name": "clerk_get_user_list",
  "arguments": {
    "organizationId": ["org_2abc123def456"],
    "limit": 100
  }
}
```

### Search with Query String
```json
{
  "name": "clerk_get_user_list",
  "arguments": {
    "query": "john doe",
    "orderBy": "last_sign_in_at",
    "limit": 20
  }
}
```

## Error Handling

All tools return proper error responses for common scenarios:

- **Missing environment variables**: Server initialization fails
- **Invalid Clerk credentials**: API calls return authentication errors
- **Invalid user IDs**: Returns 404 not found
- **Rate limiting**: Returns 429 rate limit exceeded
- **Validation errors**: Returns 400 bad request with details

## Integration with Credit Clarity

### User Registration Flow
```json
{
  "name": "clerk_create_user",
  "arguments": {
    "emailAddress": ["user@example.com"],
    "firstName": "John",
    "lastName": "Doe",
    "publicMetadata": {
      "credit_clarity_plan": "basic",
      "onboarding_completed": false,
      "credit_reports_uploaded": 0
    }
  }
}
```

### Update User After Credit Report Upload
```json
{
  "name": "clerk_update_user",
  "arguments": {
    "userId": "user_2abc123def456",
    "publicMetadata": {
      "credit_reports_uploaded": 3,
      "last_upload_date": "2025-01-15T10:30:00Z",
      "tradelines_count": 25
    }
  }
}
```

### Organization for Credit Repair Companies
```json
{
  "name": "clerk_create_organization",
  "arguments": {
    "name": "Credit Repair Experts",
    "slug": "credit-repair-experts",
    "createdBy": "user_2abc123def456",
    "publicMetadata": {
      "business_type": "credit_repair",
      "client_limit": 1000,
      "subscription_tier": "professional"
    }
  }
}
```