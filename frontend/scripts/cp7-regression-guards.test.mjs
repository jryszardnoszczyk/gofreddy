import assert from "node:assert/strict";
import test from "node:test";

import { assertCp7RegressionGuards } from "./cp7-regression-guards.mjs";

test("CP7 regression guards pass against current frontend source", () => {
  assert.doesNotThrow(() => assertCp7RegressionGuards());
});
