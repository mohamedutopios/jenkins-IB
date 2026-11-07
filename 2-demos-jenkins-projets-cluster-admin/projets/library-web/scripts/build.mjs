// "Build" de production : copie src/ dans dist/ en injectant la version
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
const version = process.env.APP_VERSION ?? 'dev';
mkdirSync('dist', { recursive: true });
for (const f of readdirSync('src')) {
  writeFileSync(`dist/${f}`, readFileSync(`src/${f}`, 'utf8').replaceAll('__VERSION__', version));
}
console.log(`dist/ genere (version ${version})`);
