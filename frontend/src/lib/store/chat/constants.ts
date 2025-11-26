import { dev } from "$app/environment";

export const WEBUI_BASE_URL = dev ? `http://${location.hostname}:8080` : ``;

export const AUDIO_API_BASE_URL = `${WEBUI_BASE_URL}/audio/api/v1`;

export const SUPPORTED_FILE_TYPE = [
  "application/epub+zip",
  "application/pdf",
  "text/plain",
  "text/csv",
  "text/xml",
  "text/html",
  "text/x-python",
  "text/css",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/octet-stream",
  "application/x-javascript",
  "text/markdown",
  "audio/mpeg",
  "audio/wav",
];

export const SUPPORTED_FILE_EXTENSIONS = [
  "md",
  "rst",
  "go",
  "py",
  "java",
  "sh",
  "bat",
  "ps1",
  "cmd",
  "js",
  "ts",
  "css",
  "cpp",
  "hpp",
  "h",
  "c",
  "cs",
  "htm",
  "html",
  "sql",
  "log",
  "ini",
  "pl",
  "pm",
  "r",
  "dart",
  "dockerfile",
  "env",
  "php",
  "hs",
  "hsc",
  "lua",
  "nginxconf",
  "conf",
  "m",
  "mm",
  "plsql",
  "perl",
  "rb",
  "rs",
  "db2",
  "scala",
  "bash",
  "swift",
  "vue",
  "svelte",
  "doc",
  "docx",
  "pdf",
  "csv",
  "txt",
  "xls",
  "xlsx",
];

// Source: https://kit.svelte.dev/docs/modules#$env-static-public
// This feature, akin to $env/static/private, exclusively incorporates environment variables
// that are prefixed with config.kit.env.publicPrefix (usually set to PUBLIC_).
// Consequently, these variables can be securely exposed to client-side code.

export const STUDENT: string = "Student";
