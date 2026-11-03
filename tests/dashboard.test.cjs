const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');

const html = readFileSync(resolve(__dirname, '../Retail_Dashboard.html'), 'utf8');
const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];

function report() {
  const ids = Object.fromEntries(['context','cards','charts','findings','period','sales-tab','ops-tab']
    .map(id => [id, { value: id === 'period' ? '2018-Q2' : '', handlers: {}, attributes: {},
      addEventListener(name, fn) { this.handlers[name] = fn; },
      setAttribute(name, value) { this.attributes[name] = value; }
    }]));
  vm.runInNewContext(script, { document: { getElementById: id => ids[id] } });
  return ids;
}

test('sales view displays the SQL totals and explains the volume/AOV tradeoff', () => {
  const d = report();
  assert.match(d.cards.innerHTML, /2,807,157/);
  assert.match(d.cards.innerHTML, /19,646/);
  assert.match(d.cards.innerHTML, /142\.89/);
  assert.match(d.findings.innerHTML, /sales rose 3\.80%/);
  assert.match(d.findings.innerHTML, /order volume fell 4\.76%/);
  assert.match(d.findings.innerHTML, /sales fell 1\.54%/);
});

test('switching to delivery shows the right service denominator and state counts', () => {
  const d = report();
  d['ops-tab'].handlers.click();
  assert.equal(d['ops-tab'].attributes['aria-pressed'], 'true');
  assert.match(d.cards.innerHTML, /19,643 delivered orders with usable dates/);
  assert.match(d.cards.innerHTML, /95\.83%/);
  assert.match(d.charts.innerHTML, /15\.63% · 25 late/);
  assert.match(d.findings.innerHTML, /SP had the most late deliveries \(207\)/);
});

test('quarter selection recalculates both views, including the year-over-year benchmark', () => {
  const d = report();
  d.period.value = '2017-Q2';
  d.period.handlers.change();
  assert.match(d.cards.innerHTML, /1,251,931/);
  assert.match(d.context.textContent, /Q2 2017/);
  d['ops-tab'].handlers.click();
  assert.match(d.cards.innerHTML, /96\.08%/);
  assert.doesNotMatch(d.findings.innerHTML, /in Q1 to/);
});
