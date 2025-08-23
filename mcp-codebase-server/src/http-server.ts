#!/usr/bin/env node

import * as http from 'http';
import * as fs from 'fs/promises';
import * as path from 'path';
import glob from 'fast-glob';
import ignore from 'ignore';

// Configuration
const CODEBASE_ROOT = process.env.CODEBASE_ROOT || '/codebase';
const MAX_FILE_SIZE = 1024 * 1024; // 1MB max file size
const MAX_SEARCH_RESULTS = 100;
const PORT = process.env.PORT || 3100;

// Utility functions
async function fileExists(filePath: string): Promise<boolean> {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readFileContent(filePath: string): Promise<string> {
  const fullPath = path.resolve(CODEBASE_ROOT, filePath);
  
  // Security check: ensure path is within codebase root
  if (!fullPath.startsWith(path.resolve(CODEBASE_ROOT))) {
    throw new Error('Path outside codebase root not allowed');
  }
  
  const stats = await fs.stat(fullPath);
  if (stats.size > MAX_FILE_SIZE) {
    throw new Error(`File too large (${stats.size} bytes, max ${MAX_FILE_SIZE})`);
  }
  
  return await fs.readFile(fullPath, 'utf-8');
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

// API handlers
async function handleReadFile(query: URLSearchParams) {
  const filePath = query.get('path');
  if (!filePath) {
    throw new Error('Missing path parameter');
  }
  
  const content = await readFileContent(filePath);
  return { file: filePath, content };
}

async function handleListFiles(query: URLSearchParams) {
  const directory = query.get('directory') || '.';
  const pattern = query.get('pattern') || '*';
  const includeHidden = query.get('include_hidden') === 'true';
  const maxDepth = parseInt(query.get('max_depth') || '5');
  
  const ig = await getGitIgnorePatterns(CODEBASE_ROOT);
  const globPattern = path.join(directory, pattern);
  
  const files = await glob(globPattern, {
    cwd: CODEBASE_ROOT,
    dot: includeHidden,
    deep: maxDepth,
    onlyFiles: true
  });
  
  const filteredFiles = files.filter(file => !ig.ignores(file));
  return { directory, files: filteredFiles, count: filteredFiles.length };
}

async function handleSearchCode(query: URLSearchParams) {
  const searchQuery = query.get('query');
  if (!searchQuery) {
    throw new Error('Missing query parameter');
  }
  
  const filePattern = query.get('file_pattern') || '**/*';
  const caseSensitive = query.get('case_sensitive') === 'true';
  const wholeWord = query.get('whole_word') === 'true';
  const contextLines = parseInt(query.get('context_lines') || '3');
  const excludeDirs = ['node_modules', '.git', '__pycache__', 'dist', 'build'];
  
  const files = await glob(filePattern, {
    cwd: CODEBASE_ROOT,
    ignore: excludeDirs.map(dir => `${dir}/**`),
    onlyFiles: true
  });
  
  const allResults = [];
  for (const file of files.slice(0, MAX_SEARCH_RESULTS)) {
    const results = await searchInFile(file, searchQuery, { 
      case_sensitive: caseSensitive, 
      whole_word: wholeWord, 
      context_lines: contextLines 
    });
    allResults.push(...results);
  }
  
  return { query: searchQuery, results: allResults, count: allResults.length };
}

async function handleGetCodebaseStructure(query: URLSearchParams) {
  const maxDepth = parseInt(query.get('max_depth') || '3');
  const showFileCount = query.get('show_file_count') !== 'false';
  
  const buildTree = async (dir: string, depth: number = 0): Promise<any[]> => {
    if (depth > maxDepth) return [];
    
    const fullPath = path.resolve(CODEBASE_ROOT, dir);
    const result = [];
    
    try {
      const entries = await fs.readdir(fullPath, { withFileTypes: true });
      const dirs = entries.filter(e => e.isDirectory() && !e.name.startsWith('.') && e.name !== 'node_modules');
      
      for (const entry of dirs) {
        const entryPath = path.join(dir, entry.name);
        const item: any = { name: entry.name, type: 'directory', depth };
        
        if (showFileCount) {
          const files = await glob('**/*', { cwd: path.resolve(CODEBASE_ROOT, entryPath), onlyFiles: true });
          item.fileCount = files.length;
        }
        
        item.children = await buildTree(entryPath, depth + 1);
        result.push(item);
      }
    } catch (error) {
      // Skip inaccessible directories
    }
    
    return result;
  };
  
  const structure = await buildTree('.');
  return { codebase: CODEBASE_ROOT, structure };
}

// HTTP Server
const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  try {
    const url = new URL(req.url!, `http://localhost:${PORT}`);
    const query = url.searchParams;
    let result: any;
    
    switch (url.pathname) {
      case '/health':
        result = { status: 'healthy', codebase: CODEBASE_ROOT, timestamp: new Date().toISOString() };
        break;
        
      case '/api/read-file':
        result = await handleReadFile(query);
        break;
        
      case '/api/list-files':
        result = await handleListFiles(query);
        break;
        
      case '/api/search-code':
        result = await handleSearchCode(query);
        break;
        
      case '/api/codebase-structure':
        result = await handleGetCodebaseStructure(query);
        break;
        
      case '/api/tools':
        result = {
          tools: [
            'read-file',
            'list-files', 
            'search-code',
            'codebase-structure'
          ]
        };
        break;
        
      default:
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Not found' }));
        return;
    }
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(result));
    
  } catch (error) {
    console.error('API Error:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: error instanceof Error ? error.message : 'Unknown error' }));
  }
});

// Start server
async function main() {
  try {
    // Validate codebase root exists
    if (!(await fileExists(CODEBASE_ROOT))) {
      throw new Error(`Codebase root does not exist: ${CODEBASE_ROOT}`);
    }
    
    server.listen(PORT, () => {
      console.log(`🚀 MCP Codebase HTTP Server started on port ${PORT}`);
      console.log(`🏗️  Serving codebase at: ${CODEBASE_ROOT}`);
      console.log(`📋 Health check: http://localhost:${PORT}/health`);
      console.log(`🔧 Available APIs:`);
      console.log(`   - GET /api/read-file?path=<file-path>`);
      console.log(`   - GET /api/list-files?directory=<dir>&pattern=<pattern>`);
      console.log(`   - GET /api/search-code?query=<search-term>`);
      console.log(`   - GET /api/codebase-structure`);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('🛑 Shutting down server...');
  server.close(() => {
    process.exit(0);
  });
});

process.on('SIGTERM', () => {
  console.log('🛑 Shutting down server...');
  server.close(() => {
    process.exit(0);
  });
});

main().catch((error) => {
  console.error('💥 Unhandled error:', error);
  process.exit(1);
});