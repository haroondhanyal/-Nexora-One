import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { screens } from '../config/screens.js';
import { lifecycleScreens } from '../config/lifecycle-screens.js';

const outputDir = resolve(fileURLToPath(new URL('../pages/', import.meta.url)));
await mkdir(outputDir, { recursive: true });
const allPages = [...screens, ...lifecycleScreens];
const pascal = (key) => key.split(/[^a-zA-Z0-9]+/).filter(Boolean).map((part) => part[0].toUpperCase() + part.slice(1)).join('');
const imports = [];
const exports = [];
const registry = [];
for (const screen of allPages) {
  const className = `${pascal(screen.key)}Page`;
  const filename = `${screen.key}.page.js`;
  imports.push(`import { ${className} } from './${filename}';`);
  exports.push(className);
  registry.push(`  ${JSON.stringify(screen.key)}: ${className},`);
  const locatorContract = JSON.parse(await readFile(resolve(outputDir, `../locators/${screen.key}.json`), 'utf8'));
  const getters = [...Object.keys(locatorContract.selectors).map((name) => `  get ${name}() { return this.locator(${JSON.stringify(name)}); }`), '  get tableCells() { return this.page.getByRole("cell"); }'].join('\n');
  await writeFile(resolve(outputDir, filename), `import { ScreenPage } from './screen-page.js';\n\nexport class ${className} extends ScreenPage {\n  constructor(page) { super(page, ${JSON.stringify(screen.key)}); }\n\n${getters}\n}\n`);
}
await writeFile(resolve(outputDir, 'screen-index.js'), `${imports.join('\n')}\n\nexport { ${exports.join(', ')} };\n\nconst pageClasses = {\n${registry.join('\n')}\n};\n\nexport function screenPageFor(page, screenKey) {\n  const PageClass = pageClasses[screenKey];\n  if (!PageClass) throw new Error(\`No page object registered for screen: \${screenKey}\`);\n  return new PageClass(page);\n}\n`);
console.log(`Generated ${allPages.length} screen page objects directly under pages/.`);
