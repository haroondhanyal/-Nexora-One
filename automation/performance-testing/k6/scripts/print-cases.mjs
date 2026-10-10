import { cases } from '../case-catalog.js';

const grouped = new Map();
for (const testCase of cases) {
  const group = `${testCase.screen} · ${testCase.method}`;
  grouped.set(group, (grouped.get(group) || 0) + 1);
}

console.log(`Nexora K6 named cases: ${cases.length}`);
for (const [group, count] of grouped) console.log(`${String(count).padStart(3)}  ${group}`);
