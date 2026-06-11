import { chromium } from 'playwright';
const b = await chromium.launch();
const ctx = await b.newContext({ httpCredentials:{username:'ora',password:'ora'}, ignoreHTTPSErrors:true });
const page = await ctx.newPage();
await page.goto('https://brandcompass-develop.oratelecom.net/',{waitUntil:'domcontentloaded',timeout:30000});
await page.waitForTimeout(1500);
const cs = await page.evaluate(()=>{ const s=getComputedStyle(document.body); const h=getComputedStyle(document.documentElement); return {bodyBg:s.backgroundColor, bodyImg:s.backgroundImage.slice(0,60), htmlClass:document.documentElement.className, bodyClass:document.body.className}; });
console.log(JSON.stringify(cs,null,2));
await b.close();
