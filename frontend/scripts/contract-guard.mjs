import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

export const criticalFiles = [
  'src/pages/ChatPage.tsx',
  'src/pages/UsagePage.tsx',
  'src/hooks/useChat.ts',
  'src/hooks/useWorkspace.ts',
  'src/hooks/useConversations.ts',
  'src/hooks/useBatchProgress.ts',
  'src/components/canvas/Canvas.tsx',
  'src/components/conversations/ConversationSidebar.tsx',
];

export const adapterFiles = [
  'src/lib/api.ts',
];

const guardedFiles = [...new Set([...criticalFiles, ...adapterFiles])];

const legacyTypeImportPatterns = [
  /from\s+["']@\/types\/api["']/,
  /from\s+["']\.\.\/types\/api["']/,
  /from\s+["']\.\/types\/api["']/,
  /from\s+["'][^"']*types\/api["']/,
];

const rawV1PathPattern = /["'`]\/?v1\//;

export function collectContractGuardFailures({ cwd = process.cwd() } = {}) {
  const failures = [];

  for (const relativePath of guardedFiles) {
    const absolutePath = resolve(cwd, relativePath);
    const content = readFileSync(absolutePath, 'utf-8');

    if (legacyTypeImportPatterns.some((pattern) => pattern.test(content))) {
      failures.push(`${relativePath}: legacy import from types/api is forbidden`);
    }

    // Adapter files are allowed to contain raw v1/ paths — they ARE the adapter
    if (!adapterFiles.includes(relativePath) && rawV1PathPattern.test(content)) {
      failures.push(`${relativePath}: raw '/v1/' endpoint string found; use api adapter functions`);
    }
  }

  return failures;
}

export function runContractGuard({ cwd = process.cwd() } = {}) {
  return collectContractGuardFailures({ cwd });
}

if (import.meta.url === new URL(`file://${process.argv[1]}`).href) {
  const failures = runContractGuard();

  if (failures.length > 0) {
    console.error('Contract guard failed:');
    for (const failure of failures) {
      console.error(`- ${failure}`);
    }
    process.exit(1);
  }

  console.log('Contract guard passed');
}
