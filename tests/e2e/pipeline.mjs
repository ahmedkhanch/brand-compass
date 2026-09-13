import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs/promises";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "../../frontend/node_modules/playwright");
const origin = process.env.AUDIT_BASE_URL || "http://127.0.0.1:4350";
const output = process.env.AUDIT_ARTIFACTS || "tests/e2e/artifacts/pipeline";
await fs.mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}) });
try {
  const context = await browser.newContext();
  await context.tracing.start({ screenshots: true, snapshots: true });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));
  const response = await page.goto(origin + "/tests", { waitUntil: "networkidle" });
  assert.equal(response.status(), 200);
  const pipeline = page.locator("#pipeline-boundary");
  assert.equal(await pipeline.count(), 1);
  assert.equal(await page.locator("#security").count(), 1);
  for (const check of ["F04A-01", "F04A-02", "F04A-03", "F04A-04", "F04A-05"]) {
    assert.ok((await pipeline.innerText()).includes(check));
  }
  assert.ok((await pipeline.innerText()).includes("Les fournisseurs externes"));
  await page.screenshot({ path: path.join(output, "pipeline-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await pipeline.scrollIntoViewIfNeeded();
  assert.ok(await pipeline.isVisible());
  await page.screenshot({ path: path.join(output, "pipeline-mobile.png"), fullPage: true });
  assert.deepEqual(errors, []);
  await context.tracing.stop({ path: path.join(output, "trace.zip") });
  await context.close();
  console.log("PASS: /tests HTTP 200; one pipeline section; five checks; security preserved; desktop/mobile; no browser errors");
} finally {
  await browser.close();
}
