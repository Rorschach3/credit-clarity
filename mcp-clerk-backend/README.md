# MCP Clerk Backend Server

A Model Context Protocol (MCP) server that provides access to Clerk's JavaScript Backend SDK for authentication and user management.

## Features

This MCP server exposes Clerk's Backend API through MCP tools, allowing you to:

### User Management
- `clerk_get_user` - Get a user by ID
- `clerk_get_user_list` - Get a list of users with filtering and pagination
- `clerk_create_user` - Create a new user
- `clerk_update_user` - Update user information
- `clerk_delete_user` - Delete a user

### Organization Management
- `clerk_get_organization` - Get an organization by ID
- `clerk_get_organization_list` - Get a list of organizations
- `clerk_create_organization` - Create a new organization

### Session Management
- `clerk_get_session` - Get a session by ID
- `clerk_get_session_list` - Get a list of sessions
- `clerk_revoke_session` - Revoke a session

### Authentication & Security
- `clerk_verify_jwt` - Verify JWT tokens
- `clerk_verify_webhook` - Verify webhook signatures

## Installation

1. Clone or copy this directory
2. Install dependencies:
```bash
npm install
```

3. Copy the environment file and configure your Clerk credentials:
```bash
cp .env.example .env
```

4. Edit `.env` with your Clerk credentials:
```env
CLERK_SECRET_KEY=sk_test_your_secret_key_here
CLERK_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

## Configuration

### Required Environment Variables

- `CLERK_SECRET_KEY` - Your Clerk Secret Key from the API keys page in the Clerk Dashboard

### Optional Environment Variables

- `CLERK_PUBLISHABLE_KEY` - Your Clerk Publishable Key
- `CLERK_JWT_KEY` - JWKS Public Key for manual JWT verification
- `CLERK_DOMAIN` - Domain for satellite applications in multi-domain setup
- `CLERK_IS_SATELLITE` - Whether this is a satellite domain (true/false)
- `CLERK_PROXY_URL` - Proxy URL for multi-domain setup
- `CLERK_API_URL` - Clerk Backend API endpoint (defaults to 'https://api.clerk.com')
- `CLERK_API_VERSION` - API version (defaults to 'v1')

## Usage

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm start
```

### With MCP Client

Add this server to your MCP client configuration:

```json
{
  "mcpServers": {
    "clerk-backend": {
      "command": "node",
      "args": ["/path/to/mcp-clerk-backend/dist/index.js"],
      "env": {
        "CLERK_SECRET_KEY": "your_secret_key"
      }
    }
  }
}
```

## Example Tool Calls

### Get User List
```json
{
  "name": "clerk_get_user_list",
  "arguments": {
    "limit": 50,
    "offset": 0,
    "orderBy": "created_at"
  }
}
```

### Create User
```json
{
  "name": "clerk_create_user",
  "arguments": {
    "emailAddress": ["user@example.com"],
    "firstName": "John",
    "lastName": "Doe",
    "password": "securepassword123"
  }
}
```

### Get User by ID
```json
{
  "name": "clerk_get_user",
  "arguments": {
    "userId": "user_12345"
  }
}
```

### Create Organization
```json
{
  "name": "clerk_create_organization",
  "arguments": {
    "name": "My Company",
    "slug": "my-company",
    "createdBy": "user_12345"
  }
}
```

### Verify JWT Token
```json
{
  "name": "clerk_verify_jwt",
  "arguments": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "audience": "my-app"
  }
}
```

## Error Handling

The server includes comprehensive error handling for:
- Missing or invalid environment variables
- Clerk API errors
- Invalid tool arguments
- Network issues

Errors are returned as MCP error responses with appropriate error codes and descriptive messages.

## Security Considerations

- Keep your `CLERK_SECRET_KEY` secure and never commit it to version control
- Use environment variables for all sensitive configuration
- The server validates all inputs using Zod schemas
- All Clerk API calls are made server-side for security

## Development

### Project Structure
```
mcp-clerk-backend/
├── src/
│   └── index.ts          # Main server implementation
├── dist/                 # Compiled JavaScript output
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── .env.example          # Example environment file
└── README.md            # This file
```

### Building
```bash
npm run build
```

### Testing
```bash
npm test
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues related to this MCP server, please create an issue in the repository.
For Clerk-specific questions, refer to the [Clerk documentation](https://clerk.com/docs).