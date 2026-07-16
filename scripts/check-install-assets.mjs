import { readFile } from "node:fs/promises";

const required = [
  ["public/argus/install.sh", "@argusevolve%2fargus"],
  ["public/argus/install.ps1", "@argusevolve%2fargus"],
  ["src/pages/release.astro", "npm install -g @argusevolve/argus@beta"],
  ["src/pages/release.astro", "https://argusbot.cn/argus/install.sh"],
  ["src/pages/release.astro", "https://argusbot.cn/argus/install.ps1"],
];

for (const [path, needle] of required) {
  const source = await readFile(path, "utf8");
  if (!source.includes(needle)) {
    throw new Error(`${path} is missing ${needle}`);
  }
  if (source.includes("@argusbot/cli")) {
    throw new Error(`${path} still references the retired npm package`);
  }
}

console.log("install assets and commands verified");
