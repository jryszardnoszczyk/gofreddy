import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { resolve } from "node:path";

const GENERATED_PATH = "src/lib/generated";

function statusEntries(cwd) {
  const output = execFileSync(
    "git",
    ["status", "--porcelain=v1", "--untracked-files=all", "--", GENERATED_PATH],
    {
      cwd,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "pipe"],
    },
  );

  return output
    .split("\n")
    .map((entry) => entry.trimEnd())
    .filter(Boolean);
}

export function assertGeneratedClean(options = {}) {
  const cwd = options.cwd ?? process.cwd();
  const entries = statusEntries(cwd);

  if (entries.length === 0) {
    return;
  }

  const message = [
    `Generated artifacts are dirty under ${GENERATED_PATH}:`,
    ...entries.map((entry) => `  ${entry}`),
    "Run `npm run api:generate` and commit the generated files.",
  ].join("\n");

  throw new Error(message);
}

function runCli() {
  try {
    assertGeneratedClean();
    console.log(`Generated artifacts are clean under ${GENERATED_PATH}`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(message);
    process.exitCode = 1;
  }
}

const invokedPath = process.argv[1] ? resolve(process.argv[1]) : "";
if (invokedPath && invokedPath === fileURLToPath(import.meta.url)) {
  runCli();
}
