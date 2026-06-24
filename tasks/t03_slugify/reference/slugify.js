const title = require('fs').readFileSync(0, 'utf8');
const slug = title
  .toLowerCase()
  .replace(/[^a-z0-9]+/g, '-')
  .replace(/^-+|-+$/g, '');
console.log(slug);
