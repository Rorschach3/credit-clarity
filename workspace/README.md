# Credit Clarity Workspace

This workspace directory contains symlinks to the package manager files and essential configuration from the `frontend/` directory.

## Symlinked Files

### Package Manager Files
- `package.json` → `../frontend/package.json`
- `package-lock.json` → `../frontend/package-lock.json`
- `node_modules/` → `../frontend/node_modules/`

### Configuration Files
- `tsconfig.json` → `../frontend/tsconfig.json`
- `vite.config.ts` → `../frontend/vite.config.ts`
- `tailwind.config.ts` → `../frontend/tailwind.config.ts`

## Usage

You can run npm/yarn commands from this workspace directory and they will use the frontend dependencies:

```bash
# From the workspace directory
npm run dev          # Start the development server
npm run build        # Build the project
npm run test         # Run tests
npm install          # Install/update dependencies
```

## Benefits

- **Centralized Access**: Access frontend package management from the root level
- **Shared Dependencies**: Uses the same node_modules as the frontend
- **Configuration Consistency**: Uses the same TypeScript and build configs
- **No Duplication**: Symlinks prevent duplicate files and keep everything in sync

## Structure

```
workspace/
├── README.md                 # This file
├── package.json             # → ../frontend/package.json
├── package-lock.json        # → ../frontend/package-lock.json
├── node_modules/            # → ../frontend/node_modules/
├── tsconfig.json           # → ../frontend/tsconfig.json
├── vite.config.ts          # → ../frontend/vite.config.ts
└── tailwind.config.ts      # → ../frontend/tailwind.config.ts
```

## Notes

- All changes made through this workspace affect the actual frontend files
- If you delete the workspace directory, no actual frontend files are lost (only symlinks)
- IDE features like IntelliSense should work normally with the symlinked files