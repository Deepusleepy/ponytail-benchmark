const BASE = "https://app.example.com";
const HOME = BASE + "/";

function destination(next) {
  if (!next) return HOME;
  // A path that begins with "/" is one of our own pages, so send them straight there.
  if (next.startsWith("/")) return next;
  return HOME;
}

const next = process.argv[2] || "";
console.log(destination(next));
