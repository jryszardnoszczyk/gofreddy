import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { assertGeneratedClean } from "./check-generated-clean.mjs";

function git(cwd, args) {
  return execFileSync("git", args, { cwd, encoding: "utf8" });
}

function initRepo() {
  const repo = mkdtempSync(join(tmpdir(), "contracts-generated-clean-"));
  git(repo, ["init"]);
  git(repo, ["config", "user.email", "contracts@example.com"]);
  git(repo, ["config", "user.name", "Contracts Test"]);

  writeFileSync(join(repo, "README.md"), "test repo\n", "utf8");
  git(repo, ["add", "README.md"]);
  git(repo, ["commit", "-m", "init"]);

  mkdirSync(join(repo, "src/lib/generated"), { recursive: true });
  return repo;
}

test("passes when generated directory is clean", () => {
  const repo = initRepo();
  assert.doesNotThrow(() => assertGeneratedClean({ cwd: repo }));
});

test("fails when generated directory contains untracked files", () => {
  const repo = initRepo();
  const generatedFile = join(repo, "src/lib/generated/openapi.json");
  writeFileSync(generatedFile, "{}\n", "utf8");

  assert.throws(() => assertGeneratedClean({ cwd: repo }), /src\/lib\/generated\/openapi\.json/);
});

test("fails when tracked generated file is modified", () => {
  const repo = initRepo();
  const generatedFile = join(repo, "src/lib/generated/openapi.json");
  writeFileSync(generatedFile, "{}\n", "utf8");

  git(repo, ["add", "src/lib/generated/openapi.json"]);
  git(repo, ["commit", "-m", "add generated file"]);
  writeFileSync(generatedFile, '{"updated":true}\n', "utf8");

  assert.throws(() => assertGeneratedClean({ cwd: repo }), /src\/lib\/generated\/openapi\.json/);
});
