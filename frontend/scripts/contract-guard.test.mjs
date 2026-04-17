import assert from 'node:assert/strict';
import test from 'node:test';

import {
  adapterFiles,
  collectContractGuardFailures,
  criticalFiles,
} from './contract-guard.mjs';

test('contract guard includes PR-031 canvas surfaces and adapter coverage', () => {
  assert(criticalFiles.includes('src/pages/ChatPage.tsx'));
  assert(criticalFiles.includes('src/hooks/useWorkspace.ts'));
  assert(criticalFiles.includes('src/components/canvas/Canvas.tsx'));
  assert(adapterFiles.includes('src/lib/api.ts'));
});

test('contract guard passes against current frontend source', () => {
  assert.deepEqual(collectContractGuardFailures(), []);
});
