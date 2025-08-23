#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import * as fs from 'fs/promises';
import * as path from 'path';
import glob from 'fast-glob';
import ignore from 'ignore';

// Configuration
const CODEBASE_ROOT = process.env.CODEBASE_ROOT || '/mnt/c/projects/credit-clarity';
const MAX_FILE_SIZE = 1024 * 1024; // 1MB max file size
const MAX_SEARCH_RESULTS = 100;

// Tool definitions
const TOOLS = [
  // File operations
  {
    name: 'read_file',
    description: 'Read contents of a specific file in the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Relative path to the file from codebase root' }
      },
      required: ['path']
    }
  },
  {
    name: 'list_files',
    description: 'List files in a directory with optional filtering',
    inputSchema: {
      type: 'object',
      properties: {
        directory: { type: 'string', description: 'Directory path (relative to codebase root)', default: '.' },
        pattern: { type: 'string', description: 'Glob pattern to filter files', default: '*' },
        include_hidden: { type: 'boolean', description: 'Include hidden files/directories', default: false },
        max_depth: { type: 'number', description: 'Maximum directory depth to traverse', default: 5 }
      }
    }
  },
  
  // Search operations
  {
    name: 'search_code',
    description: 'Search for code patterns, functions, classes, or text across the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Search query (supports regex)' },
        file_pattern: { type: 'string', description: 'File pattern to search in (e.g., "*.py", "*.ts")', default: '**/*' },
        case_sensitive: { type: 'boolean', description: 'Case sensitive search', default: false },
        whole_word: { type: 'boolean', description: 'Match whole words only', default: false },
        context_lines: { type: 'number', description: 'Number of context lines around matches', default: 3 },
        exclude_dirs: { type: 'array', items: { type: 'string' }, description: 'Directories to exclude', default: ['node_modules', '.git', '__pycache__', 'dist', 'build'] }
      },
      required: ['query']
    }
  },
  {
    name: 'find_functions',
    description: 'Find function definitions across the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Function name to search for' },
        language: { type: 'string', description: 'Programming language (python, typescript, javascript)', default: 'all' },
        include_methods: { type: 'boolean', description: 'Include class methods', default: true }
      },
      required: ['name']
    }
  },
  {
    name: 'find_classes',
    description: 'Find class definitions across the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Class name to search for' },
        language: { type: 'string', description: 'Programming language (python, typescript, javascript)', default: 'all' }
      },
      required: ['name']
    }
  },
  
  // Analysis operations
  {
    name: 'analyze_imports',
    description: 'Analyze import/require statements in files',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: { type: 'string', description: 'Path to file to analyze' },
        show_unused: { type: 'boolean', description: 'Attempt to identify unused imports', default: false }
      },
      required: ['file_path']
    }
  },
  {
    name: 'get_file_dependencies',
    description: 'Get dependencies of a specific file (what it imports and what imports it)',
    inputSchema: {
      type: 'object',
      properties: {
        file_path: { type: 'string', description: 'Path to file to analyze' }
      },
      required: ['file_path']
    }
  },
  {
    name: 'get_codebase_structure',
    description: 'Get high-level structure of the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        max_depth: { type: 'number', description: 'Maximum directory depth', default: 3 },
        show_file_count: { type: 'boolean', description: 'Show file counts per directory', default: true }
      }
    }
  },
  
  // Git operations
  {
    name: 'git_status',
    description: 'Get git status of the codebase',
    inputSchema: {
      type: 'object',
      properties: {
        show_untracked: { type: 'boolean', description: 'Show untracked files', default: true }
      }
    }
  },
  {
    name: 'git_log',
    description: 'Get recent git commits',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Number of commits to show', default: 10 },
        file_path: { type: 'string', description: 'Show commits for specific file' }
      }
    }
  },
  
  // Documentation operations
  {
    name: 'find_todos',
    description: 'Find TODO, FIXME, HACK, and other code comments',
    inputSchema: {
      type: 'object',
      properties: {
        types: { type: 'array', items: { type: 'string' }, description: 'Types of comments to find', default: ['TODO', 'FIXME', 'HACK', 'NOTE', 'BUG'] },
        file_pattern: { type: 'string', description: 'File pattern to search', default: '**/*' }
      }
    }
  },
  {
    name: 'get_api_endpoints',
    description: 'Find API endpoints in the codebase (routes, handlers)',
    inputSchema: {
      type: 'object',
      properties: {
        framework: { type: 'string', description: 'Framework to look for (fastapi, express, flask)', default: 'all' }
      }
    }
  }
] as const;

// Utility functions
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function isDirectory(path: string): Promise<boolean> {
  try {
    const stats = await fs.stat(path);
    return stats.isDirectory();
  } catch {
    return false;
  }
}

async function getGitIgnorePatterns(rootPath: string): Promise<any> {
  const ig = ignore();
  const gitignorePath = path.join(rootPath, '.gitignore');
  
  try {
    const gitignoreContent = await fs.readFile(gitignorePath, 'utf-8');
    ig.add(gitignoreContent);
  } catch {
    // No .gitignore file
  }
  
  // Add common patterns
  ig.add([
    'node_modules/**',
    '.git/**',
    '__pycache__/**',
    '*.pyc',
    '.DS_Store',
    'dist/**',
    'build/**',
    '.vscode/**',
    '.idea/**',
    '*.log'
  ]);
  
  return ig;
}

async function readFileContent(filePath: string): Promise<string> {
  const fullPath = path.resolve(CODEBASE_ROOT, filePath);
  
  // Security check: ensure path is within codebase root
  if (!fullPath.startsWith(path.resolve(CODEBASE_ROOT))) {
    throw new McpError(ErrorCode.InvalidParams, 'Path outside codebase root not allowed');
  }
  
  const stats = await fs.stat(fullPath);
  if (stats.size > MAX_FILE_SIZE) {
    throw new McpError(ErrorCode.InvalidParams, `File too large (${stats.size} bytes, max ${MAX_FILE_SIZE})`);
  }
  
  return await fs.readFile(fullPath, 'utf-8');
}

async function searchInFile(filePath: string, query: string, options: any): Promise<any[]> {
  try {
    const content = await readFileContent(filePath);
    const lines = content.split('\n');
    const results = [];
    
    const regex = new RegExp(
      options.whole_word ? `\\b${query}\\b` : query,
      options.case_sensitive ? 'g' : 'gi'
    );
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const matches = line.match(regex);
      if (matches) {
        const contextStart = Math.max(0, i - options.context_lines);
        const contextEnd = Math.min(lines.length - 1, i + options.context_lines);
        
        results.push({
          file: filePath,
          line: i + 1,
          content: line.trim(),
          context: lines.slice(contextStart, contextEnd + 1).map((l, idx) => ({
            line: contextStart + idx + 1,
            content: l,
            isMatch: contextStart + idx === i
          }))
        });
      }
    }
    
    return results;
  } catch (error) {
    return [];
  }
}

// Create and configure the server
const server = new Server({
  name: 'mcp-codebase-server',
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
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'read_file': {
        const { path: filePath } = args as { path: string };
        const content = await readFileContent(filePath);
        
        return {
          content: [
            {
              type: 'text',
              text: `File: ${filePath}\n${'='.repeat(50)}\n${content}`,
            },
          ],
        };
      }

      case 'list_files': {
        const { directory = '.', pattern = '*', include_hidden = false, max_depth = 5 } = args as any;
        const searchPath = path.resolve(CODEBASE_ROOT, directory);
        
        const ig = await getGitIgnorePatterns(CODEBASE_ROOT);
        
        const globPattern = path.join(directory, pattern);
        const files = await glob(globPattern, {
          cwd: CODEBASE_ROOT,
          dot: include_hidden,
          deep: max_depth,
          onlyFiles: true
        });
        
        const filteredFiles = files.filter(file => !ig.ignores(file));
        
        return {
          content: [
            {
              type: 'text',
              text: `Files in ${directory} (${filteredFiles.length} files):\n${filteredFiles.map(f => `  ${f}`).join('\n')}`,
            },
          ],
        };
      }

      case 'search_code': {
        const { 
          query, 
          file_pattern = '**/*', 
          case_sensitive = false, 
          whole_word = false, 
          context_lines = 3,
          exclude_dirs = ['node_modules', '.git', '__pycache__', 'dist', 'build']
        } = args as any;
        
        const files = await glob(file_pattern, {
          cwd: CODEBASE_ROOT,
          ignore: exclude_dirs.map((dir: string) => `${dir}/**`),
          onlyFiles: true
        });
        
        const allResults = [];
        for (const file of files.slice(0, MAX_SEARCH_RESULTS)) {
          const results = await searchInFile(file, query, { case_sensitive, whole_word, context_lines });
          allResults.push(...results);
        }
        
        const output = allResults.length > 0 
          ? allResults.map(result => 
              `📁 ${result.file}:${result.line}\n` +
              `${result.context.map((ctx: any) => 
                `${ctx.isMatch ? '→' : ' '} ${ctx.line}: ${ctx.content}`
              ).join('\n')}\n`
            ).join('\n')
          : 'No matches found.';
        
        return {
          content: [
            {
              type: 'text',
              text: `Search results for "${query}" (${allResults.length} matches):\n${'='.repeat(50)}\n${output}`,
            },
          ],
        };
      }

      case 'find_functions': {
        const { name: functionName, language = 'all', include_methods = true } = args as any;
        
        const patterns = {
          python: [`def ${functionName}\\s*\\(`],
          typescript: [`function ${functionName}\\s*\\(`, `const ${functionName}\\s*=`, `${functionName}\\s*\\(`],
          javascript: [`function ${functionName}\\s*\\(`, `const ${functionName}\\s*=`, `${functionName}\\s*\\(`]
        };
        
        const searchPatterns = language === 'all' 
          ? Object.values(patterns).flat()
          : patterns[language as keyof typeof patterns] || [];
        
        const filePatterns = language === 'all' 
          ? '**/*.{py,ts,tsx,js,jsx}'
          : language === 'python' 
            ? '**/*.py'
            : '**/*.{ts,tsx,js,jsx}';
        
        const allResults = [];
        for (const pattern of searchPatterns) {
          const files = await glob(filePatterns, { cwd: CODEBASE_ROOT, onlyFiles: true });
          
          for (const file of files.slice(0, 50)) {
            const results = await searchInFile(file, pattern, { case_sensitive: false, whole_word: false, context_lines: 5 });
            allResults.push(...results);
          }
        }
        
        const output = allResults.length > 0
          ? allResults.map(result => `📁 ${result.file}:${result.line}\n  ${result.content}`).join('\n')
          : `No functions named "${functionName}" found.`;
        
        return {
          content: [
            {
              type: 'text',
              text: `Function definitions for "${functionName}":\n${'='.repeat(50)}\n${output}`,
            },
          ],
        };
      }

      case 'get_codebase_structure': {
        const { max_depth = 3, show_file_count = true } = args as any;
        
        const buildTree = async (dir: string, depth: number = 0): Promise<string> => {
          if (depth > max_depth) return '';
          
          const fullPath = path.resolve(CODEBASE_ROOT, dir);
          let result = '';
          
          try {
            const entries = await fs.readdir(fullPath, { withFileTypes: true });
            const dirs = entries.filter(e => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules');
            
            for (const entry of dirs) {
              const entryPath = path.join(dir, entry.name);
              const indent = '  '.repeat(depth);
              
              if (show_file_count) {
                const files = await glob('**/*', { cwd: path.resolve(CODEBASE_ROOT, entryPath), onlyFiles: true });
                result += `${indent}📁 ${entry.name}/ (${files.length} files)\n`;
              } else {
                result += `${indent}📁 ${entry.name}/\n`;
              }
              
              result += await buildTree(entryPath, depth + 1);
            }
          } catch (error) {
            // Skip inaccessible directories
          }
          
          return result;
        };
        
        const structure = await buildTree('.');
        
        return {
          content: [
            {
              type: 'text',
              text: `Codebase Structure:\n${'='.repeat(50)}\n${structure}`,
            },
          ],
        };
      }

      case 'find_todos': {
        const { types = ['TODO', 'FIXME', 'HACK', 'NOTE', 'BUG'], file_pattern = '**/*' } = args as any;
        
        const commentPattern = types.map((type: string) => `(${type}|${type.toLowerCase()})`).join('|');
        const regex = `(//|#|/\\*)\\s*(${commentPattern})\\s*:?\\s*(.*)`;
        
        const files = await glob(file_pattern, {
          cwd: CODEBASE_ROOT,
          ignore: ['node_modules/**', '.git/**'],
          onlyFiles: true
        });
        
        const allResults = [];
        for (const file of files.slice(0, 100)) {
          const results = await searchInFile(file, regex, { case_sensitive: false, whole_word: false, context_lines: 1 });
          allResults.push(...results);
        }
        
        const output = allResults.length > 0
          ? allResults.map(result => `📁 ${result.file}:${result.line}\n  ${result.content}`).join('\n')
          : 'No TODO comments found.';
        
        return {
          content: [
            {
              type: 'text',
              text: `TODO Comments Found (${allResults.length}):\n${'='.repeat(50)}\n${output}`,
            },
          ],
        };
      }

      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error) {
    throw new McpError(
      ErrorCode.InternalError,
      `Tool execution failed: ${error instanceof Error ? error.message : String(error)}`
    );
  }
});

// Initialize and start the server
async function main() {
  try {
    // Validate codebase root exists
    if (!(await fileExists(CODEBASE_ROOT))) {
      throw new Error(`Codebase root does not exist: ${CODEBASE_ROOT}`);
    }
    
    console.error(`🏗️  MCP Codebase Server starting for: ${CODEBASE_ROOT}`);
    
    // Start the server
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('🚀 MCP Codebase Server started successfully');
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', async () => {
  console.error('🛑 Shutting down MCP Codebase Server...');
  await server.close();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.error('🛑 Shutting down MCP Codebase Server...');
  await server.close();
  process.exit(0);
});

main().catch((error) => {
  console.error('💥 Unhandled error:', error);
  process.exit(1);
});