// env_utils.ts
// this utility will check a students setup to verify it has
// packages loaded, node installed and api keys available
// it references the package.json file and example.env for requirements

import fs from "node:fs";
import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);

// ========== NODE ENVIRONMENT DIAGNOSTICS ==========
function checkNodeExecutableAndVersion(): {
  success: boolean;
  nodeVersion: string;
  issues: string[];
} {
  const issues: string[] = [];
  const nodeVersion = process.version;

  console.log("=".repeat(70));
  console.log("NODE ENVIRONMENT DIAGNOSTICS");
  console.log("=".repeat(70));
  console.log(`Node executable: ${process.execPath}`);
  console.log(`Node version: ${nodeVersion}`);
  console.log(`Platform: ${process.platform}`);
  console.log();

  // Check Node version (require >= 18)
  const major = parseInt(nodeVersion.slice(1).split(".")[0], 10);
  if (major < 18) {
    issues.push(`\u26a0\ufe0f  Node ${nodeVersion} is below minimum required version v18`);
  } else {
    console.log(`\u2705 Node version ${nodeVersion} is supported (>=18)`);
  }

  // Check if npm/npx are available
  try {
    execSync("npm --version", { stdio: "pipe" });
    console.log("\u2705 npm is available");
  } catch {
    issues.push("\u26a0\ufe0f  npm not found in PATH");
  }

  // Check if tsx is available
  try {
    execSync("npx tsx --version", { stdio: "pipe" });
    console.log("\u2705 tsx is available");
  } catch {
    issues.push(
      "\u26a0\ufe0f  tsx not found — install it with: npm install -g tsx"
    );
  }

  if (issues.length > 0) {
    console.log("\n" + "!".repeat(70));
    console.log("POTENTIAL ISSUES DETECTED:");
    console.log("!".repeat(70));
    for (const issue of issues) {
      console.log(issue);
    }
    console.log("\nRECOMMENDATION:");
    console.log("  Make sure Node.js >= 18 is installed");
    console.log("  Run: npm install");
    console.log("!".repeat(70));
  }

  console.log();
  return { success: issues.length === 0, nodeVersion, issues };
}

// ========== HELPER FUNCTIONS ==========

function summarizeValue(
  key: string,
  value: string,
  exampleValue?: string
): string {
  const lower = value.toLowerCase();
  if (lower === "true" || lower === "false") return lower;

  const isApiKey = key.endsWith("API_KEY");
  if (!isApiKey) return value;

  // For API_KEY variables, show full value if it matches the example (needs changing)
  if (exampleValue && value === exampleValue) return value;

  // Otherwise, obscure the API key
  return value.length > 4 ? "****" + value.slice(-4) : "****" + value;
}

function parseRequiredKeys(
  exampleFilePath: string
): Record<string, string> {
  if (!fs.existsSync(exampleFilePath)) return {};

  const content = fs.readFileSync(exampleFilePath, "utf-8");
  const requiredKeys: Record<string, string> = {};
  let isRequiredSection = false;

  for (const line of content.split("\n")) {
    const stripped = line.trim();
    if (stripped.startsWith("#")) {
      isRequiredSection = stripped.toLowerCase().includes("required");
    } else if (stripped.includes("=") && !stripped.startsWith("#")) {
      const key = stripped.split("=")[0].trim();
      let value = stripped.split("=").slice(1).join("=").trim();
      if (
        (value.startsWith("'") && value.endsWith("'")) ||
        (value.startsWith('"') && value.endsWith('"'))
      ) {
        value = value.slice(1, -1);
      }
      if (isRequiredSection) {
        requiredKeys[key] = value;
      }
    }
  }
  return requiredKeys;
}

function checkEnvFileExists(
  envFilePath = ".env",
  exampleFilePath = "example.env"
): boolean {
  if (fs.existsSync(envFilePath)) return true;

  if (!fs.existsSync(exampleFilePath)) {
    console.log(
      "\u26a0\ufe0f  No .env file found and no example.env to check against"
    );
    console.log(`   Run: cp example.env .env`);
    console.log();
    return false;
  }

  const requiredKeys = parseRequiredKeys(exampleFilePath);
  const found: Record<string, string> = {};
  const missing: string[] = [];

  for (const [key] of Object.entries(requiredKeys)) {
    const sysVal = process.env[key];
    if (sysVal !== undefined) {
      if (sysVal.includes("your_") || sysVal.includes("_here")) {
        missing.push(key);
      } else {
        found[key] = sysVal;
      }
    } else {
      missing.push(key);
    }
  }

  console.log("=".repeat(70));
  console.log("\u26a0\ufe0f  NO .env FILE FOUND");
  console.log("=".repeat(70));

  if (missing.length > 0 && Object.keys(found).length === 0) {
    console.log(
      "No .env file found and required variables are not set in system environment."
    );
    console.log();
    console.log("Required variables not set:");
    for (const key of missing) {
      console.log(`  - ${key}`);
    }
    console.log();
    console.log("SOLUTION: Create a .env file from the example:");
    console.log("  cp example.env .env");
    console.log("  Then edit .env with your API keys.");
  } else if (missing.length > 0) {
    console.log(
      "No .env file found. Some required variables found in system environment,"
    );
    console.log("but others are missing.");
    console.log();
    console.log("Using system environment values for:");
    for (const key of Object.keys(found)) {
      console.log(`  \u2705 ${key}`);
    }
    console.log();
    console.log("Missing:");
    for (const key of missing) {
      console.log(`  \u26a0\ufe0f  ${key}`);
    }
    console.log();
    console.log("SOLUTION: Create a .env file from the example:");
    console.log("  cp example.env .env");
    console.log("  Then edit .env with your API keys.");
  } else {
    console.log(
      "No .env file found, but all required variables are set in system environment."
    );
    console.log();
    console.log("Using system environment values for:");
    for (const key of Object.keys(found)) {
      console.log(`  \u2705 ${key}`);
    }
    console.log();
    console.log("NOTE: You can still create a .env file if preferred:");
    console.log("  cp example.env .env");
  }

  console.log("=".repeat(70));
  console.log();
  return false;
}

function checkEnvConflicts(envFilePath: string): void {
  if (!fs.existsSync(envFilePath)) return;

  // Parse the .env file manually
  const envContent = fs.readFileSync(envFilePath, "utf-8");
  const envFileVars: Record<string, string> = {};
  for (const line of envContent.split("\n")) {
    const stripped = line.trim();
    if (stripped && !stripped.startsWith("#") && stripped.includes("=")) {
      const key = stripped.split("=")[0].trim();
      let value = stripped.split("=").slice(1).join("=").trim();
      if (
        (value.startsWith("'") && value.endsWith("'")) ||
        (value.startsWith('"') && value.endsWith('"'))
      ) {
        value = value.slice(1, -1);
      }
      envFileVars[key] = value;
    }
  }

  const conflicts: { key: string; systemValue: string; fileValue: string }[] =
    [];
  for (const [key, fileValue] of Object.entries(envFileVars)) {
    const sysValue = process.env[key];
    if (sysValue !== undefined && sysValue !== fileValue) {
      conflicts.push({ key, systemValue: sysValue, fileValue });
    }
  }

  if (conflicts.length > 0) {
    console.log("=".repeat(70));
    console.log("\u26a0\ufe0f  ENVIRONMENT VARIABLE CONFLICTS DETECTED");
    console.log("=".repeat(70));
    console.log(
      "The following environment variables are already set in your system"
    );
    console.log(
      "environment and differ from your .env file. The system values will be used."
    );
    console.log();
    for (const conflict of conflicts) {
      console.log(`Variable: ${conflict.key}`);
      if (conflict.key.endsWith("API_KEY")) {
        const sysVal =
          conflict.systemValue.length > 4
            ? "****" + conflict.systemValue.slice(-4)
            : "****";
        const fileVal =
          conflict.fileValue.length > 4
            ? "****" + conflict.fileValue.slice(-4)
            : "****";
        console.log(`  System value: ${sysVal}`);
        console.log(`  .env value:   ${fileVal}`);
      } else {
        console.log(`  System value: ${conflict.systemValue}`);
        console.log(`  .env value:   ${conflict.fileValue}`);
      }
      console.log();
    }

    console.log("SOLUTIONS:");
    console.log(
      "  1. Unset the conflicting system environment variables:"
    );
    for (const conflict of conflicts) {
      console.log(`       unset ${conflict.key}`);
    }
    console.log();
    console.log(
      "  2. Use dotenv with override option in your scripts"
    );
    console.log();
    console.log(
      "  3. Update your .env file to match your system environment"
    );
    console.log("=".repeat(70));
    console.log();
  }
}

function checkManualInstalls(filePath: string): void {
  if (!fs.existsSync(filePath)) return;

  const content = fs.readFileSync(filePath, "utf-8");
  let manualInstalls: string[] = [];

  for (const line of content.split("\n")) {
    const stripped = line.trim();
    if (stripped.startsWith("# Manual installs for checking:")) {
      const appsStr = stripped.split(":").slice(1).join(":").trim();
      if (appsStr) {
        manualInstalls = appsStr.split(",").map((s) => s.trim());
      }
      break;
    }
  }

  if (manualInstalls.length === 0) return;

  const issues: string[] = [];
  const found: string[] = [];

  for (const app of manualInstalls) {
    try {
      execSync(`which ${app}`, { stdio: "pipe" });
      found.push(`\u2705 ${app}`);
    } catch {
      issues.push(`\u26a0\ufe0f  ${app} not found in PATH`);
    }
  }

  console.log("Manual Installs Check:");
  for (const item of found) console.log(item);
  for (const issue of issues) console.log(issue);
  console.log();
}

function doublecheckEnv(filePath: string): void {
  if (!fs.existsSync(filePath)) {
    console.log(`Did not find file ${filePath}.`);
    console.log(
      "This is used to double check the key settings for the notebook."
    );
    console.log("This is just a check and is not required.\n");
    return;
  }

  const requiredKeys = parseRequiredKeys(filePath);

  // Parse all example values
  const allExampleValues: Record<string, string> = {};
  const content = fs.readFileSync(filePath, "utf-8");
  for (const line of content.split("\n")) {
    const stripped = line.trim();
    if (stripped.includes("=") && !stripped.startsWith("#")) {
      const key = stripped.split("=")[0].trim();
      let value = stripped.split("=").slice(1).join("=").trim();
      if (
        (value.startsWith("'") && value.endsWith("'")) ||
        (value.startsWith('"') && value.endsWith('"'))
      ) {
        value = value.slice(1, -1);
      }
      allExampleValues[key] = value;
    }
  }

  const issues: string[] = [];
  const printedKeys = new Set<string>();

  console.log("Environment Variables:");

  for (const key of Object.keys(allExampleValues)) {
    const current = process.env[key];
    const exampleVal = allExampleValues[key];

    if (current !== undefined) {
      console.log(`${key}=${summarizeValue(key, current, exampleVal)}`);

      if (
        key in requiredKeys &&
        current === exampleVal &&
        exampleVal &&
        (exampleVal.includes("your_") || exampleVal.includes("_here"))
      ) {
        issues.push(
          `  \u26a0\ufe0f  ${key} still has the example/placeholder value`
        );
      }
    } else {
      console.log(`${key}=<not set>`);
      if (key in requiredKeys) {
        issues.push(`  \u26a0\ufe0f  ${key} is required but not set`);
      }
    }

    printedKeys.add(key);
  }

  // Special check for LangSmith tracing
  const langsmithTracing = (
    process.env.LANGSMITH_TRACING || ""
  ).toLowerCase();
  const langsmithApiKey = process.env.LANGSMITH_API_KEY || "";
  const langsmithExample = allExampleValues["LANGSMITH_API_KEY"] || "";

  if (langsmithTracing === "true") {
    if (!langsmithApiKey) {
      issues.push(
        `  \u26a0\ufe0f  LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY is not set`
      );
    } else if (langsmithApiKey === langsmithExample) {
      issues.push(
        `  \u26a0\ufe0f  LANGSMITH_TRACING is enabled but LANGSMITH_API_KEY still has the example/placeholder value`
      );
    }
  }

  if (issues.length > 0) {
    console.log("\nIssues found:");
    for (const issue of issues) {
      console.log(issue);
    }
  }
  console.log();
}

// ========== Check packages based on package.json ==========

function doublecheckPkgs(
  packageJsonPath = "package.json",
  verbose = false
): void {
  if (!fs.existsSync(packageJsonPath)) {
    console.log(`ERROR: ${packageJsonPath} not found.`);
    return;
  }

  const data = JSON.parse(fs.readFileSync(packageJsonPath, "utf-8"));
  const deps = {
    ...data.dependencies,
    ...data.devDependencies,
  } as Record<string, string>;

  if (Object.keys(deps).length === 0) {
    if (verbose) {
      console.log("No dependencies found in package.json.");
    }
    return;
  }

  const problems: { pkg: string; required: string; status: string }[] = [];
  const results: {
    pkg: string;
    required: string;
    installed: string;
    status: string;
  }[] = [];

  for (const [pkg, required] of Object.entries(deps)) {
    let installed = "-";
    let status = "\u274c Missing";

    try {
      const pkgJsonPath = path.join("node_modules", pkg, "package.json");
      if (fs.existsSync(pkgJsonPath)) {
        const pkgData = JSON.parse(fs.readFileSync(pkgJsonPath, "utf-8"));
        installed = pkgData.version || "-";
        status = "\u2705 OK";
      }
    } catch {
      // keep defaults
    }

    results.push({ pkg, required, installed, status });
    if (status !== "\u2705 OK") {
      problems.push({ pkg, required, status });
    }
  }

  if (verbose || problems.length > 0) {
    // Print table
    const headers = ["package", "required", "installed", "status"];
    const rows = results.map((r) => [r.pkg, r.required, r.installed, r.status]);
    const widths = headers.map((h, i) =>
      Math.max(h.length, ...rows.map((row) => row[i].length))
    );

    const fmtRow = (cols: string[]) =>
      cols.map((c, i) => c.padEnd(widths[i])).join(" | ");

    console.log(fmtRow(headers));
    console.log(fmtRow(widths.map((w) => "-".repeat(w))));
    for (const row of rows) {
      console.log(fmtRow(row));
    }

    if (problems.length > 0) {
      console.log("\nIssues detected:");
      for (const r of problems) {
        console.log(`- ${r.pkg}: ${r.status} (required ${r.required})`);
      }
      console.log("\nRun: npm install");
    }
  }
}

// ========== MAIN ==========

// Run diagnostics
checkNodeExecutableAndVersion();

// Check manual installs
checkManualInstalls("example.env");

// Check if .env file exists
const envExists = checkEnvFileExists(".env", "example.env");

if (envExists) {
  // Load .env file
  const dotenv = await import("dotenv");
  dotenv.config();

  // Check for environment conflicts
  checkEnvConflicts(".env");
}

// Check environment variables and API keys
doublecheckEnv("example.env");

// Check packages
doublecheckPkgs("package.json", true);
