import fs from "fs";
import { exec } from "child_process";
import { fileURLToPath } from "url";
import path from "path";
import { config } from "dotenv";

// Load .env file
config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Create directory if it doesn't exist
const openapiDir = path.join(__dirname, "..", "openapi");
if (!fs.existsSync(openapiDir)) {
  fs.mkdirSync(openapiDir, { recursive: true });
}

// Get API URL from environment variable
const baseUrl = process.env.VITE_DJANGO_API_URL;
if (!baseUrl) {
  console.error("Error: VITE_DJANGO_API_URL environment variable is not set");
  process.exit(1);
}

// Fetch OpenAPI schema from the backend
const apiUrl = `${baseUrl}/_api/openapi.json`;
const outputFile = path.join(openapiDir, "openapi.json");

console.log(`Fetching OpenAPI schema from ${apiUrl}`);
console.log(`Saving to ${outputFile}`);

exec(`curl -sf ${apiUrl} -o ${outputFile}`, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error fetching OpenAPI schema: ${error.message}`);
    process.exit(1);
  }
  if (stderr) {
    console.error(`Error: ${stderr}`);
    process.exit(1);
  }

  // Verify the file was downloaded and is valid JSON
  try {
    const content = fs.readFileSync(outputFile, "utf-8");
    JSON.parse(content);
    console.log(`OpenAPI schema successfully saved to ${outputFile}`);
  } catch (parseError) {
    console.error(`Error: Downloaded file is not valid JSON`);
    process.exit(1);
  }
});
