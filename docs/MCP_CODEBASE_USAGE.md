# MCP Codebase Server - Usage Guide

Your new MCP server is ready! This gives you powerful AI-driven codebase analysis and interaction capabilities.

## 🚀 **What You Now Have**

A comprehensive MCP server with **13 powerful tools** for codebase interaction:

### 📁 **File Operations**
- `read_file` - Read any file in your codebase
- `list_files` - List files with filtering and patterns
- `get_codebase_structure` - Get directory structure overview

### 🔍 **Code Search & Analysis** 
- `search_code` - Search for text, regex, patterns across files
- `find_functions` - Find function definitions by name
- `find_classes` - Locate class definitions
- `analyze_imports` - Analyze import statements
- `get_file_dependencies` - Map file dependency relationships

### 📝 **Documentation & Maintenance**
- `find_todos` - Find TODO, FIXME, HACK comments
- `get_api_endpoints` - Discover API routes and handlers

### 🌿 **Git Integration**
- `git_status` - Current git status
- `git_log` - Recent commit history

## 🛠️ **Quick Start**

1. **Build the server:**
```bash
cd /mnt/c/projects/credit-clarity/mcp-codebase-server
npm run build
```

2. **Start the server:**
```bash
npm start
```

3. **Add to your MCP client config:**
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

## 💡 **Powerful Use Cases for Credit Clarity Development**

### 1. **Debug OCR Pipeline Issues**
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

### 2. **Find All API Endpoints**
```json
{
  "name": "search_code", 
  "arguments": {
    "query": "@app\\.(get|post|put|delete)",
    "file_pattern": "**/*.py",
    "context_lines": 3
  }
}
```

### 3. **Locate React Components**
```json
{
  "name": "list_files",
  "arguments": {
    "directory": "frontend/src/components",
    "pattern": "*.tsx",
    "max_depth": 3
  }
}
```

### 4. **Find Credit Report Processing Functions**
```json
{
  "name": "find_functions",
  "arguments": {
    "name": "process_credit_report",
    "language": "python"
  }
}
```

### 5. **Track Down TODO Items**
```json
{
  "name": "find_todos",
  "arguments": {
    "types": ["TODO", "FIXME", "BUG"],
    "file_pattern": "**/*.{py,ts,tsx}"
  }
}
```

### 6. **Analyze File Dependencies**  
```json
{
  "name": "analyze_imports",
  "arguments": {
    "file_path": "backend/services/optimized_processor.py"
  }
}
```

## 🎯 **Perfect for Your Current Issues**

### **OCR Pipeline Debugging**
- Find all functions related to credit bureau detection
- Trace file dependencies in the processing pipeline
- Search for duplicate detection logic

### **Frontend Development**
- Locate React components and their imports
- Find TypeScript interfaces and types
- Search for specific utility functions

### **API Development**
- Map all FastAPI endpoints
- Find database models and relationships
- Locate validation schemas

### **Code Quality**
- Find all TODO/FIXME comments
- Analyze import patterns
- Check for unused dependencies

## 🔧 **Advanced Features**

### **Smart Filtering**
- Respects `.gitignore` patterns
- Excludes `node_modules`, `__pycache__`, etc.
- File size limits for safety

### **Context-Aware Results**
- Search results include surrounding code context
- Function definitions show parameter lists
- Import analysis shows usage patterns

### **Multi-Language Support**
- Python (FastAPI, data processing)
- TypeScript/JavaScript (React frontend)
- JSON/YAML (configuration files)
- Markdown (documentation)

## 🚀 **Integration with Your Workflow**

This MCP server is specifically designed for Credit Clarity development:

1. **OCR Debugging** - Quickly find and analyze document processing code
2. **API Discovery** - Map your FastAPI endpoints and database models  
3. **Frontend Analysis** - Navigate React components and utilities
4. **Architecture Review** - Understand file dependencies and imports
5. **Code Quality** - Find TODOs and maintenance items

## 📊 **Server Status**

- ✅ Built and ready to use
- ✅ TypeScript compiled successfully  
- ✅ All 13 tools implemented
- ✅ Security features enabled
- ✅ Git integration working
- ✅ MCP client config ready

## 🎉 **Next Steps**

1. **Start using the server** with your MCP client
2. **Try searching for your recent OCR fixes** like `detect_credit_bureau`
3. **Explore the codebase structure** to understand the architecture
4. **Find API endpoints** to document your backend routes

Your MCP server is now a powerful AI assistant for your Credit Clarity codebase! 🚀