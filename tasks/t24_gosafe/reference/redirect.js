const BASE = "https://app.example.com";
const HOME = BASE + "/";

function destination(next) {
  if (!next) return HOME;
  let resolved;
  try {
    resolved = new URL(next, BASE);
  } catch (e) {
    return HOME;
  }
  if (resolved.origin !== BASE) return HOME;
  return resolved.href;
}

const next = process.argv[2] || "";
console.log(destination(next));
