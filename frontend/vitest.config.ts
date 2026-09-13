import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  test: {
    environment: "node",
    include: ["tests/unit/**/*.test.tsx"],
    coverage: {
      provider: "v8",
      include: ["src/app/tests/page.tsx"],
      reporter: ["text", "lcov"],
      reportsDirectory: process.env.COVERAGE_DIR || "coverage",
      thresholds: { lines: 100 },
    },
  },
});
