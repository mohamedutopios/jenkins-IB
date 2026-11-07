// Controle minimal : pas de console.log oublie dans src/
import { readdirSync, readFileSync } from 'node:fs';
const fautes = readdirSync('src')
  .filter((f) => f.endsWith('.mjs'))
  .filter((f) => readFileSync(`src/${f}`, 'utf8').includes('console.log'));
if (fautes.length) {
  console.error(`console.log interdit dans : ${fautes.join(', ')}`);
  process.exit(1);
}
console.log('lint OK');
