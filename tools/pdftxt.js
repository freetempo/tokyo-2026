ObjC.import('Foundation');
ObjC.import('Quartz');
function run(argv) {
  const url = $.NSURL.fileURLWithPath($(argv[0]));
  const doc = $.PDFDocument.alloc.initWithURL(url);
  if (!doc.js) { return 'ERROR: 讀不到 PDF'; }
  const n = doc.pageCount;
  let out = [];
  const from = argv[1] ? parseInt(argv[1]) - 1 : 0;
  const to   = argv[2] ? parseInt(argv[2]) : n;
  for (let i = from; i < Math.min(to, n); i++) {
    const p = doc.pageAtIndex(i);
    out.push('===== p' + (i + 1) + ' =====\n' + (p.string.js || ''));
  }
  return out.join('\n');
}
