# MCP Codebase Server

A comprehensive Model Context Protocol (MCP) server for analyzing and interacting with your Credit Clarity codebase.

## Features

This MCP server provides powerful tools for LLM-codebase interaction:

### 📁 **File Operations**
- `read_file` - Read contents of any file in the codebase
- `list_files` - List files with filtering and glob patterns
- `get_codebase_structure` - Get high-level directory structure

### 🔍 **Code Search & Analysis**
- `search_code` - Search for text, patterns, or regex across files
- `find_functions` - Locate function definitions by name
- `find_classes` - Find class definitions across languages
- `analyze_imports` - Analyze import/require statements
- `get_file_dependencies` - Map file dependencies

### 📝 **Documentation & Maintenance**
- `find_todos` - Find TODO, FIXME, HACK comments
- `get_api_endpoints` - Discover API routes and handlers

### 🌿 **Git Integration**
- `git_status` - Get current git status
- `git_log` - View recent commits

## Installation

1. Navigate to the server directory:
```bash
cd /mnt/c/projects/credit-clarity/mcp-codebase-server
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment (optional):
```bash
cp .env.example .env
# Edit .env if you need custom paths
```

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

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "codebase": {
      "command": "node",
      "args": ["/mnt/c/projects/credit-clarity/mcp-codebase-server/dist/index.js"],
      "env": {
        "CODEBASE_ROOT": "/mnt/c/projects/credit-clarity"
      }
    }
  }
}
```

## Example Tool Calls

### Read a specific file
```json
{
  "name": "read_file",
  "arguments": {
    "path": "backend/services/optimized_processor.py"
  }
}
```

### Search for code patterns
```json
{
  "name": "search_code",
  "arguments": {
    "query": "detect_credit_bureau",
    "file_pattern": "**/*.py",
    "context_lines": 5
  }
}
```

### Find function definitions
```json
{
  "name": "find_functions",
  "arguments": {
    "name": "process_credit_report",
    "language": "python"
  }
}
```

### List files in a directory
```json
{
  "name": "list_files",
  "arguments": {
    "directory": "frontend/src/components",
    "pattern": "*.tsx",
    "max_depth": 2
  }
}
```

### Get codebase structure
```json
{
  "name": "get_codebase_structure",
  "arguments": {
    "max_depth": 3,
    "show_file_count": true
  }
}
```

### Find TODO comments
```json
{
  "name": "find_todos",
  "arguments": {
    "types": ["TODO", "FIXME", "BUG"],
    "file_pattern": "**/*.{py,ts,tsx}"
  }
}
```

## Configuration

### Environment Variables

- `CODEBASE_ROOT` - Root directory of your codebase (default: `/mnt/c/projects/credit-clarity`)
- `MAX_FILE_SIZE` - Maximum file size to read in bytes (default: 1MB)
- `MAX_SEARCH_RESULTS` - Maximum search results to return (default: 100)

### Supported File Types

The server automatically handles:
- **Python**: `.py` files
- **TypeScript/JavaScript**: `.ts`, `.tsx`, `.js`, `.jsx` files
- **Configuration**: `.json`, `.yaml`, `.yml`, `.toml` files
- **Documentation**: `.md`, `.txt` files
- **And many more...**

### Intelligent Filtering

The server respects:
- `.gitignore` patterns
- Common ignore patterns (node_modules, __pycache__, etc.)
- File size limits
- Directory depth limits

## Advanced Features

### Context-Aware Search
Search results include surrounding context lines for better understanding.

### Multi-Language Support
Detects and handles Python, TypeScript, JavaScript with appropriate syntax patterns.

### Git Integration
Provides git status and history information for better development context.

### Security Features
- Path traversal protection
- File size limits
- Configurable access boundaries

## Perfect for Credit Clarity Development

This server is specifically designed for the Credit Clarity codebase with:
- **Backend Analysis**: Python FastAPI services, database models
- **Frontend Analysis**: React/TypeScript components, utilities
- **OCR Pipeline**: Document processing, tradeline extraction
- **API Discovery**: Route mapping, endpoint documentation
- **Architecture Review**: Import analysis, dependency mapping

## Development

### Project Structure
```
mcp-codebase-server/
├── src/
│   └── index.ts          # Main server implementation
├── dist/                 # Compiled JavaScript
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md            # This file
```

### Building
```bash
npm run build
```

### Watching for Changes
```bash
npm run watch
```

## License

MIT License - Part of the Credit Clarity project.

## Contributing

This MCP server is designed specifically for Credit Clarity's development workflow. Contributions should focus on improving codebase analysis and LLM interaction capabilities.