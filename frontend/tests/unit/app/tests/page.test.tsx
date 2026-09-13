import { expect, test } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import TestsPage from "@/app/tests/page";

test("central validation preserves security and exposes the pipeline evidence once", () => {
  const html = renderToStaticMarkup(<TestsPage />);
  expect(html.match(/id="pipeline-boundary"/g)).toHaveLength(1);
  expect(html).toContain("F04A-01");
  expect(html).toContain("F04A-02");
  expect(html).toContain("F04A-03");
  expect(html).toContain("id=\"security\"");
  expect(html).toContain("Les fournisseurs externes");
  expect(html).toContain("Swagger /docs");
});
