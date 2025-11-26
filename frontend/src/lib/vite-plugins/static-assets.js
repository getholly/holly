import { readFileSync } from "fs";
import { join } from "path";

/**
 * Custom Vite plugin to handle static assets with "static/" prefix
 */
export function staticAssetsPlugin() {
  const rootDir = process.cwd();
  const staticDir = join(rootDir, "static");

  return {
    name: "vite-plugin-static-assets",

    // Handle asset references during build
    resolveId(id, importer) {
      if (id.startsWith("static/")) {
        const relativePath = id.replace("static/", "");
        const fullPath = join(staticDir, relativePath);
        return fullPath;
      }
      return null;
    },

    // Configure dev server to handle static/ requests
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        // Handle both /static/ and root-level paths (like /img/)
        if (
          req.url &&
          (req.url.startsWith("/static/") ||
            req.url.startsWith("/img/") ||
            req.url.startsWith("/favicon."))
        ) {
          try {
            let relativePath;
            if (req.url.startsWith("/static/")) {
              relativePath = req.url.replace("/static/", "");
            } else {
              // For paths like /img/file.png, serve from static/img/file.png
              relativePath = req.url.substring(1); // Remove leading /
            }

            const fullPath = join(staticDir, relativePath);

            // Determine content type based on file extension
            const contentType = getContentType(fullPath);

            // Serve the file
            const fileContent = readFileSync(fullPath);
            res.setHeader("Content-Type", contentType);
            res.setHeader("Cache-Control", "public, max-age=3600");
            res.end(fileContent);

            return;
          } catch (err) {
            console.error(`Error serving static file: ${err.message}`);
          }
        }
        next();
      });
    },
  };
}

/**
 * Get MIME type based on file extension
 */
function getContentType(filePath) {
  const ext = filePath.split(".").pop().toLowerCase();

  switch (ext) {
    case "png":
      return "image/png";
    case "jpg":
    case "jpeg":
      return "image/jpeg";
    case "gif":
      return "image/gif";
    case "svg":
      return "image/svg+xml";
    case "css":
      return "text/css";
    case "js":
      return "application/javascript";
    case "json":
      return "application/json";
    case "txt":
      return "text/plain";
    case "webp":
      return "image/webp";
    case "ico":
      return "image/x-icon";
    case "pdf":
      return "application/pdf";
    case "woff":
      return "font/woff";
    case "woff2":
      return "font/woff2";
    case "ttf":
      return "font/ttf";
    case "otf":
      return "font/otf";
    default:
      return "application/octet-stream";
  }
}
