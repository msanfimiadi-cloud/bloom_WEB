import { cp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const dist = join(root, 'dist');
const distAssets = join(dist, 'assets');

const rewriteHtmlForDist = (html) => html
  .replace(/href=["']\/src\/styles\.css["']/g, 'href="/assets/styles.css"')
  .replace(/src=["']\/src\/main\.js["']/g, 'src="/assets/main.js"');

await rm(dist, { recursive: true, force: true });
await mkdir(distAssets, { recursive: true });

await cp(join(root, 'public', 'assets'), distAssets, { recursive: true });
await cp(join(root, 'src', 'main.js'), join(distAssets, 'main.js'));
await cp(join(root, 'src', 'styles.css'), join(distAssets, 'styles.css'));

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

console.log('frontend build completed');
