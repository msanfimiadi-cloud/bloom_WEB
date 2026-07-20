import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const dist = join(root, 'dist');

const rewriteHtmlForDist = (html) => html
  .replace(/href=["']\/src\/styles\.css["']/g, 'href="/assets/styles.css"')
  .replace(/src=["']\/src\/main\.js["']/g, 'src="/assets/main.js"');

await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });

// Everything under public is a deployable public resource. Copying the whole
// directory prevents legal pages and other non-asset files from silently
// disappearing from the production build.
await cp(join(root, 'public'), dist, { recursive: true });
// Legacy Word documents are retained in the repository for reference only.
// The reviewed HTML documents below are the only legal texts published.
await rm(join(dist, 'docs'), { recursive: true, force: true });
await cp(join(root, 'src', 'main.js'), join(dist, 'assets', 'main.js'));
await cp(join(root, 'src', 'styles.css'), join(dist, 'assets', 'styles.css'));

const indexHtml = await readFile(join(root, 'index.html'), 'utf-8');
await writeFile(join(dist, 'index.html'), rewriteHtmlForDist(indexHtml));
await writeFile(join(dist, 'build-info.json'), JSON.stringify({ builtAt: new Date().toISOString() }, null, 2));

const distIndex = await readFile(join(dist, 'index.html'), 'utf-8');
if (distIndex.includes('/src/main.js') || distIndex.includes('/src/styles.css')) {
  throw new Error('Build verification failed: dist/index.html still contains /src references');
}

const hasJsAsset = /src=["']\/assets\/.+\.js["']/.test(distIndex);
const hasCssAsset = /href=["']\/assets\/.+\.css["']/.test(distIndex);
if (!hasJsAsset || !hasCssAsset) {
  throw new Error('Build verification failed: dist/index.html missing /assets JS/CSS references');
}

const requiredPublicFiles = [
  'offer/index.html',
  'privacy/index.html',
  'terms/index.html',
  'personal-data-consent/index.html',
  'legal.css',
];

for (const publicFile of requiredPublicFiles) {
  await readFile(join(dist, publicFile));
}

console.log('frontend build completed');
