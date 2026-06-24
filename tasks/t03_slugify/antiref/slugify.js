'use strict';

const fs = require('fs');

// Transliteration table so accented letters degrade to plain ASCII.
const CHAR_MAP = {
  à: 'a', á: 'a', â: 'a', ä: 'a', ã: 'a', å: 'a',
  è: 'e', é: 'e', ê: 'e', ë: 'e',
  ì: 'i', í: 'i', î: 'i', ï: 'i',
  ò: 'o', ó: 'o', ô: 'o', ö: 'o', õ: 'o',
  ù: 'u', ú: 'u', û: 'u', ü: 'u',
  ñ: 'n', ç: 'c', ß: 'ss',
};

const DEFAULT_OPTIONS = {
  separator: '-',
  lowercase: true,
  transliterate: true,
  maxLength: 0,
  trim: true,
};

class Slugifier {
  constructor(options) {
    this.options = Object.assign({}, DEFAULT_OPTIONS, options || {});
  }

  applyCase(text) {
    return this.options.lowercase ? text.toLowerCase() : text;
  }

  transliterate(text) {
    if (!this.options.transliterate) {
      return text;
    }
    let out = '';
    for (const ch of text) {
      out += Object.prototype.hasOwnProperty.call(CHAR_MAP, ch) ? CHAR_MAP[ch] : ch;
    }
    return out;
  }

  collapse(text) {
    const sep = this.options.separator;
    const escaped = sep.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    let out = text.replace(/[^a-z0-9]+/gi, sep);
    if (this.options.trim) {
      const edge = new RegExp('^(?:' + escaped + ')+|(?:' + escaped + ')+$', 'g');
      out = out.replace(edge, '');
    }
    return out;
  }

  truncate(text) {
    if (!this.options.maxLength || text.length <= this.options.maxLength) {
      return text;
    }
    const sep = this.options.separator;
    let cut = text.slice(0, this.options.maxLength);
    const idx = cut.lastIndexOf(sep);
    if (idx > 0) {
      cut = cut.slice(0, idx);
    }
    return cut;
  }

  slugify(input) {
    let text = String(input);
    text = this.applyCase(text);
    text = this.transliterate(text);
    text = this.collapse(text);
    text = this.truncate(text);
    return text;
  }
}

function slugify(input, options) {
  return new Slugifier(options).slugify(input);
}

function main() {
  const title = fs.readFileSync(0, 'utf8');
  process.stdout.write(slugify(title) + '\n');
}

main();

module.exports = { Slugifier, slugify, DEFAULT_OPTIONS, CHAR_MAP };
