const fs = require("fs");
const path = require("path");
const ts = require("typescript");

const root = path.join(process.cwd(), "apps", "web");
const files = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === "node_modules" || entry.name === ".next") continue;
      walk(p);
    } else if (/\.(ts|tsx)$/.test(entry.name) && !entry.name.endsWith(".d.ts")) {
      files.push(p);
    }
  }
}
walk(root);

const errors = [];
for (const file of files) {
  const text = fs.readFileSync(file, "utf8");
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, file.endsWith(".tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
  for (const diagnostic of source.parseDiagnostics) {
    const lc = source.getLineAndCharacterOfPosition(diagnostic.start || 0);
    errors.push(`${file}:${lc.line + 1}:${lc.character + 1} ${ts.flattenDiagnosticMessageText(diagnostic.messageText, " ")}`);
  }
  function visit(node) {
    if (ts.isObjectLiteralExpression(node)) {
      const seen = new Map();
      for (const prop of node.properties) {
        if (!(ts.isPropertyAssignment(prop) || ts.isShorthandPropertyAssignment(prop) || ts.isMethodDeclaration(prop)) || !prop.name) continue;
        const name = prop.name.getText(source).replace(/^['"]|['"]$/g, "");
        if (seen.has(name)) {
          const lc = source.getLineAndCharacterOfPosition(prop.getStart(source));
          errors.push(`${file}:${lc.line + 1}:${lc.character + 1} duplicate object-literal key ${name}`);
        } else {
          seen.set(name, true);
        }
      }
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
}

if (errors.length) {
  console.error(errors.join("\n"));
  process.exit(1);
}
console.log(`Frontend AST check: PASS (${files.length} TS/TSX source files; no parse diagnostics or duplicate object keys)`);

const browserFiles = [
  "playwright.config.ts",
  "e2e/public-smoke.spec.ts",
  "e2e/accessibility.spec.ts",
  "e2e/security.spec.ts",
];
for (const rel of browserFiles) {
  if (!fs.existsSync(path.join(root, rel))) throw new Error(`missing browser certification file: ${rel}`);
}
console.log(`Browser certification harness: PASS (${browserFiles.length} files present)`);
