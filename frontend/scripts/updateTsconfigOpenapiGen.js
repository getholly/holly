import fs from "fs";
import path from "path";

const tsconfigPath = path.join(
  process.cwd(),
  "gen",
  "openapi",
  "tsconfig.json",
);
const tsconfig = JSON.parse(
  fs.readFileSync(tsconfigPath, { encoding: "utf-8" }),
);

tsconfig.compilerOptions.lib = ["es2017", "DOM", "DOM.Iterable"];

fs.writeFileSync(tsconfigPath, JSON.stringify(tsconfig, null, 2));
