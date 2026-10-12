const path = require('path');
const fs = require('fs');
const { createExtractorFromFile } = require('node-unrar-js');

function iterate(v) {
  const out = [];
  if (Array.isArray(v)) return v;
  if (v && typeof v.next === 'function') { let r; while (!(r = v.next()).done) out.push(r.value); return out; }
  if (v && typeof v[Symbol.iterator] === 'function') return [...v];
  throw new Error('cannot iterate');
}

async function main() {
  const outDir = path.resolve(process.argv[3]);
  const extractor = await createExtractorFromFile({ filepath: path.resolve(process.argv[2]), targetPath: outDir });
  const all = iterate(extractor.getFileList().fileHeaders).filter(h => !h.flags.directory);
  const pick = h => h.name.startsWith('已往作业/第4课/8班/') || h.name.startsWith('课程资料/第04课');
  const targets = all.filter(pick).map(h => h.name);

  const res = extractor.extract({ files: targets });
  const files = res && res.files ? iterate(res.files) : [];
  console.log('returned=' + files.length);
  if (files.length) console.log('file keys=' + JSON.stringify(Object.keys(files[0])));
  let written = 0;
  for (const fe of files) {
    const name = fe.fileHeader.name;
    const data = fe.extraction;
    if (!data) continue;
    const dest = path.join(outDir, name);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.writeFileSync(dest, Buffer.from(data));
    written++;
  }
  console.log('written=' + written);
}

main().catch(e => { console.error('ERR ' + (e && e.stack || e)); process.exit(1); });