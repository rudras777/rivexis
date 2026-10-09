import {test} from 'node:test';
import assert from 'node:assert/strict';
import {brandedPdf} from './report-pdf.mjs';
test('vector report header preserves byte-exact PDF structure and escapes financial text',()=>{
  const bytes=brandedPdf('RIVEXIS evidence',['Collateral (USD): $30,000','Source: a\\b','Unicode: →']);
  const pdf=new TextDecoder().decode(bytes);
  assert.ok(pdf.startsWith('%PDF-1.4'));
  assert.ok(!pdf.includes('/Subtype /Image'));
  assert.ok(pdf.includes('0.21 0 0 -0.21 72 768 cm'));
  assert.ok(pdf.includes('(Collateral \\(USD\\): $30,000) Tj'));
  assert.ok(pdf.includes('(Source: a\\\\b) Tj'));
  const content=pdf.match(/\/Length (\d+) >> stream\n([\s\S]*?)\nendstream/);
  assert.equal(new TextEncoder().encode(content[2]).length,Number(content[1]));
  const offset=Number(pdf.match(/startxref\n(\d+)/)[1]);assert.equal(pdf.slice(offset,offset+4),'xref');
  for(const row of pdf.matchAll(/^(\d{10}) 00000 n /gm))assert.match(pdf.slice(Number(row[1])),/^\d+ 0 obj /);
});
