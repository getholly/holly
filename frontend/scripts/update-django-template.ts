// Improved version with debugging
import fs from "fs/promises";
import path from "path";
import { JSDOM } from "jsdom";

// --- Configuration ---
// Path to the SvelteKit build output directory (relative to SvelteKit project root)
const svelteKitBuildDir = "./build";
const svelteKitIndexPath = path.join(svelteKitBuildDir, "index.html");

// Path to your source Django template file (relative to SvelteKit project root)
const djangoTemplatePath =
  "../githubme/githubme/templates/holly/holly-svelte-template.html";

// Path where the updated Django template will be saved (relative to SvelteKit project root)
const outputDjangoTemplatePath =
  "../githubme/githubme/templates/holly/generated_svelte_host.html";

// Directory in your Django project where SvelteKit static assets should be copied
const djangoStaticDir = "/holly";
const djangoStaticTargetDir = `../githubme/static/${djangoStaticDir}`;

// URL prefix to use inside Django's {% static %} tags
const djangoStaticUrlPrefix = "";

// Markers in the Django template for JS script injection
const jsStartMarker = "<!-- insert svelte startup code here -->";
const jsEndMarker = "<!-- end svelte startup code -->";

// Django static adapter script path (relative to SvelteKit static directory)
const djangoAdapterScriptPath = "_app/django-static-adapter.js";

// Markers in the Django template for preload links injection
// If these don't exist, we'll add preload links to the head section via javascript block
const preloadStartMarker = "<!-- insert svelte preload links here -->";
const preloadEndMarker = "<!-- end svelte preload links -->";
// --- End Configuration ---

/**
 * Cleans asset paths from SvelteKit's index.html for use in Django's static tag.
 * Example: /_app/immutable/... -> _app/immutable/...
 * @param assetPath The original path from SvelteKit's index.html
 * @returns Cleaned path suitable for Django's static tag
 */
function cleanAssetPath(assetPath: string | null): string {
  if (!assetPath) {
    return "";
  }
  // Remove leading slash if present
  return assetPath.startsWith("/") ? assetPath.substring(1) : assetPath;
}

/**
 * Joins URL parts, ensuring no double slashes and handling empty parts.
 * @param parts Array of URL parts to join
 * @returns A single string with parts joined by '/'
 */
function joinUrlParts(...parts: string[]): string {
  return parts
    .map((part) => part.trim().replace(/^\/+|\/+$/g, "")) // Remove leading/trailing slashes from each part
    .filter((part) => part !== "") // Filter out empty parts
    .join("/");
}

/**
 * Recursively copies files and directories from source to destination.
 * Excludes top-level .html files from the source directory.
 * @param sourceDir Source directory path
 * @param targetDir Target directory path
 */
async function copySvelteKitAssets(sourceDir: string, targetDir: string) {
  console.log(`Copying SvelteKit assets from ${sourceDir} to ${targetDir}...`);
  await fs.mkdir(targetDir, { recursive: true }); // Ensure target directory exists

  const entries = await fs.readdir(sourceDir, { withFileTypes: true });

  for (const entry of entries) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);

    if (entry.isDirectory()) {
      await fs.cp(sourcePath, targetPath, { recursive: true });
      console.log(`Copied directory: ${sourcePath} to ${targetPath}`);
    } else if (!entry.name.endsWith(".html")) {
      // Exclude .html files at the root of build
      await fs.copyFile(sourcePath, targetPath);
      console.log(`Copied file: ${sourcePath} to ${targetPath}`);
    } else {
      console.log(`Skipped HTML file: ${sourcePath}`);
    }
  }
}

/**
 * Generates a small JavaScript adapter to make SvelteKit use Django static URLs
 * This will be loaded by the Django template and patch SvelteKit's import system
 */
async function generateDjangoAdapter() {
  console.log("Generating Django static adapter for SvelteKit...");

  const adapterPath = path.join(djangoStaticTargetDir, djangoAdapterScriptPath);

  const adapterCode = `
/**
 * Django Static Adapter for SvelteKit
 * This module patches the import system to use Django static URLs
 */

// Store the original import function
const originalDynamicImport = window.import;

// Create a function to convert paths to Django static URLs
function pathToDjangoStaticUrl(path) {
    // If the path already includes static, don't modify it
    if (path.includes('/static/')) {
        return path;
    }

    // Remove leading slash if present
    const cleanPath = path.startsWith('/') ? path.substring(1) : path;

    // For _app and other SvelteKit paths, add the Django static prefix
    if (cleanPath.startsWith('_app/')) {
        return \`/static/${djangoStaticUrlPrefix}/\${cleanPath}\`;
    }

    return path;
}

// Patch the dynamic import function
window.import = function(path) {
    const djangoPath = pathToDjangoStaticUrl(path);
    console.log(\`SvelteKit import: \${path} -> \${djangoPath}\`);
    return originalDynamicImport.call(window, djangoPath);
};

console.log('Django Static Adapter for SvelteKit initialized');
`;

  // Make sure directory exists
  const adapterDir = path.dirname(adapterPath);
  await fs.mkdir(adapterDir, { recursive: true });

  // Write the adapter file
  await fs.writeFile(adapterPath, adapterCode, "utf-8");

  console.log(`Django Static Adapter written to: ${adapterPath}`);
}

async function main() {
  console.log("Starting Django template update process...");

  try {
    // --- Asset Copying Step ---
    console.log(
      `Cleaning and preparing Django static target directory: ${djangoStaticTargetDir}`,
    );
    await fs.rm(djangoStaticTargetDir, { recursive: true, force: true }); // Remove old assets
    await fs.mkdir(djangoStaticTargetDir, { recursive: true }); // Recreate directory

    // Copy SvelteKit build assets (excluding index.html and other .html files at root)
    await copySvelteKitAssets(svelteKitBuildDir, djangoStaticTargetDir);
    console.log("SvelteKit assets copied to Django static directory.");

    // Generate the Django adapter script
    await generateDjangoAdapter();
    console.log("Generated Django static adapter script.");
    // --- End Asset Copying Step ---

    // 1. Read SvelteKit's index.html
    console.log(`Reading SvelteKit index.html from: ${svelteKitIndexPath}`);
    const svelteKitHtmlContent = await fs.readFile(svelteKitIndexPath, "utf-8");

    // 2. Parse SvelteKit's index.html using JSDOM
    const dom = new JSDOM(svelteKitHtmlContent);
    const document = dom.window.document;

    // 3. Extract modulepreload links, CSS links, and JS script tags
    const modulePreloadLinks: string[] = [];
    const cssLinks: string[] = [];

    // Process all modulepreload links
    document
      .querySelectorAll('link[rel="modulepreload"]')
      .forEach((linkElement) => {
        const rawHref = linkElement.getAttribute("href");
        const cleanedHref = cleanAssetPath(rawHref);
        if (cleanedHref) {
          const staticPathInTag = joinUrlParts(
            djangoStaticUrlPrefix,
            cleanedHref,
          );
          const integrity = linkElement.getAttribute("integrity");
          const crossorigin = linkElement.getAttribute("crossorigin");
          let linkTag = `<link rel="modulepreload" href="{% static '${staticPathInTag}' %}"`;
          if (integrity) linkTag += ` integrity="${integrity}"`;
          if (crossorigin) linkTag += ` crossorigin="${crossorigin}"`;
          linkTag += `>`;
          modulePreloadLinks.push(linkTag);
          console.log(
            `Processed modulepreload for template: ${staticPathInTag}`,
          );
        }
      });

    // Extended CSS selector to match more stylesheet patterns
    document
      .querySelectorAll('link[rel="stylesheet"], link[href*=".css"]')
      .forEach((linkElement) => {
        const rawHref = linkElement.getAttribute("href");
        const cleanedHref = cleanAssetPath(rawHref);
        if (cleanedHref) {
          const staticPathInTag = joinUrlParts(
            djangoStaticUrlPrefix,
            cleanedHref,
          );
          const integrity = linkElement.getAttribute("integrity");
          const crossorigin = linkElement.getAttribute("crossorigin");
          let linkTag = `<link rel="stylesheet" href="{% static '${staticPathInTag}' %}"`;
          if (integrity) linkTag += ` integrity="${integrity}"`;
          if (crossorigin) linkTag += ` crossorigin="${crossorigin}"`;
          linkTag += `>`;
          cssLinks.push(linkTag);
          console.log(`Processed CSS for template: ${staticPathInTag}`);
        }
      });

    const jsScripts: string[] = [];

    // Extended script selector to match more JS patterns
    document.querySelectorAll("script[src]").forEach((scriptElement) => {
      const rawSrc = scriptElement.getAttribute("src");
      const cleanedSrc = cleanAssetPath(rawSrc);
      if (cleanedSrc) {
        const staticPathInTag = joinUrlParts(djangoStaticUrlPrefix, cleanedSrc);
        const integrity = scriptElement.getAttribute("integrity");
        const crossorigin = scriptElement.getAttribute("crossorigin");
        const isModule =
          scriptElement.hasAttribute("type") &&
          scriptElement.getAttribute("type") === "module";
        const isNoModule = scriptElement.hasAttribute("nomodule");

        let scriptTag = `<script`;
        if (isModule) scriptTag += ` type="module"`;
        if (isNoModule) scriptTag += ` nomodule`;
        scriptTag += ` src="{% static '${staticPathInTag}' %}"`;
        if (integrity) scriptTag += ` integrity="${integrity}"`;
        if (crossorigin) scriptTag += ` crossorigin="${crossorigin}"`;
        scriptTag += ` defer></script>`;
        jsScripts.push(scriptTag);
        console.log(`Processed JS script for template: ${staticPathInTag}`);
      }
    });

    // Add the code for extracting inline scripts with imports (SvelteKit's startup script)
    document.querySelectorAll("script:not([src])").forEach((scriptElement) => {
      const content = scriptElement.textContent || "";

      // Looking for SvelteKit's initialization pattern
      if (
        content.includes("__sveltekit") &&
        content.includes("import(") &&
        content.includes("_app/immutable/entry/")
      ) {
        // This is the SvelteKit initialization script
        // We'll need to transform it to use Django's static template tag while keeping the structure

        // First extract the base value
        const baseMatch = content.match(/base:\s*"([^"]*)"/);
        const base = baseMatch ? baseMatch[1] : "";

        // Extract the import paths using regex
        const importRegex = /import\s*\(\s*["']([^"']+)["']\s*\)/g;
        let match;
        const importPaths: string[] = [];

        while ((match = importRegex.exec(content)) !== null) {
          if (match[1]) {
            importPaths.push(match[1]);
          }
        }

        // Create a new script that works with our Django static adapter
        // We need to ensure it uses the static URLs properly
        let djanjoSvelteInitScript = `<script>
 {
  // Use a simplified init approach that works with our static adapter
  __sveltekit_1dwrf1s = {
   base: ""
  };

  const element = document.currentScript.parentElement;

  // These imports will be intercepted by our Django static adapter
  Promise.all([`;

        // Add the import statements with Django static tags instead of original paths
        const importStatements = importPaths.map((importPath) => {
          if (importPath.startsWith("http")) {
            return `import('${importPath}')`;
          }
          const cleanedPath = cleanAssetPath(importPath);
          const staticPathInTag = joinUrlParts(
            djangoStaticUrlPrefix,
            cleanedPath,
          );
          return `   import("{% static '${djangoStaticDir}/${staticPathInTag}' %}")`;
        });

        djanjoSvelteInitScript += "\n" + importStatements.join(",\n");

        djanjoSvelteInitScript += `
  ]).then(([kit, app]) => {
   kit.start(app, element);
  });
 }
</script>`;

        // Add this script directly to jsScripts
        jsScripts.push(djanjoSvelteInitScript);
        console.log(
          "Added SvelteKit initialization script with Django static tags",
        );

        // We should also add modulepreload links for these imports
        for (const importPath of importPaths) {
          const cleanedPath = cleanAssetPath(importPath);
          if (cleanedPath) {
            const staticPathInTag = joinUrlParts(
              djangoStaticUrlPrefix,
              cleanedPath,
            );
            const preloadTag = `<link rel="modulepreload" href="{% static '${staticPathInTag}' %}">`;
            modulePreloadLinks.push(preloadTag);
            console.log(
              `Added modulepreload for SvelteKit entry point: ${staticPathInTag}`,
            );
          }
        }
      }
      // Also handle any other script imports
      else if (
        content.includes("import(") &&
        content.includes("_app/immutable/")
      ) {
        // Extract the import paths using regex
        const importRegex = /import\\s*\\(\\s*[\"']([^\"']+)[\"']\\s*\\)/g;
        let match;

        while ((match = importRegex.exec(content)) !== null) {
          if (match[1]) {
            const cleanedPath = cleanAssetPath(match[1]);
            if (cleanedPath) {
              const staticPathInTag = joinUrlParts(
                djangoStaticUrlPrefix,
                cleanedPath,
              );
              const preloadTag = `<link rel="modulepreload" href="{% static '${staticPathInTag}' %}">`;
              modulePreloadLinks.push(preloadTag);
              console.log(
                `Added modulepreload for script import: ${staticPathInTag}`,
              );
            }
          }
        }
      }
    });

    // 4. Check if we found any assets
    if (
      modulePreloadLinks.length === 0 &&
      cssLinks.length === 0 &&
      jsScripts.length === 0
    ) {
      console.warn(
        "Warning: No CSS or JS assets found in SvelteKit's index.html. Check build output.",
      );

      // Fallback: Look for _app directory assets
      const appDir = path.join(svelteKitBuildDir, "_app");

      if (
        await fs
          .stat(appDir)
          .then(() => true)
          .catch(() => false)
      ) {
        console.log("Looking for assets in _app directory as fallback...");

        // Try to find entry point JS files directly
        try {
          const appFiles = await fs.readdir(appDir, { recursive: true });

          // Find possible entry JS files (look for common patterns in SvelteKit builds)
          const jsEntryFiles = appFiles
            .filter(
              (file) =>
                typeof file === "string" &&
                file.endsWith(".js") &&
                (file.includes("entry") || file.includes("start")),
            )
            .map((file) =>
              typeof file === "string"
                ? path.join("_app", file)
                : path.join("_app", file.toString()),
            );

          for (const jsFile of jsEntryFiles) {
            const staticPathInTag = joinUrlParts(djangoStaticUrlPrefix, jsFile);
            const scriptTag = `<script type="module" src="{% static '${staticPathInTag}' %}" defer></script>`;
            jsScripts.push(scriptTag);
            console.log(`Added fallback JS entry point: ${staticPathInTag}`);
          }

          // Look for CSS files
          const cssFiles = appFiles
            .filter((file) => typeof file === "string" && file.endsWith(".css"))
            .map((file) =>
              typeof file === "string"
                ? path.join("_app", file)
                : path.join("_app", file.toString()),
            );

          for (const cssFile of cssFiles) {
            const staticPathInTag = joinUrlParts(
              djangoStaticUrlPrefix,
              cssFile,
            );
            const linkTag = `<link rel="stylesheet" href="{% static '${staticPathInTag}' %}">`;
            cssLinks.push(linkTag);
            console.log(`Added fallback CSS: ${staticPathInTag}`);
          }

          // Find chunk JS files to add as modulepreload
          const jsChunkFiles = appFiles
            .filter(
              (file) =>
                typeof file === "string" &&
                file.endsWith(".js") &&
                file.includes("chunks"),
            )
            .map((file) =>
              typeof file === "string"
                ? path.join("_app", file)
                : path.join("_app", file.toString()),
            );

          for (const jsChunk of jsChunkFiles) {
            const staticPathInTag = joinUrlParts(
              djangoStaticUrlPrefix,
              jsChunk,
            );
            const linkTag = `<link rel="modulepreload" href="{% static '${staticPathInTag}' %}">`;
            modulePreloadLinks.push(linkTag);
            console.log(`Added fallback chunk preload: ${staticPathInTag}`);
          }
        } catch (error) {
          console.warn("Failed to process fallback assets:", error);
        }
      }
    }

    // 5. Read the Django template file
    console.log(`Reading Django template from: ${djangoTemplatePath}`);
    let djangoTemplateContent = await fs.readFile(djangoTemplatePath, "utf-8");

    // 6. Inject modified CSS links into {% block javascript %}
    const cssBlockEndMarker = "{% endblock javascript%}";
    const cssBlockEndIndex = djangoTemplateContent.indexOf(cssBlockEndMarker);
    if (cssBlockEndIndex !== -1) {
      // Try to preserve indentation from the line of cssBlockEndMarker
      const linesBeforeEndBlock = djangoTemplateContent
        .substring(0, cssBlockEndIndex)
        .split("\n");
      const lastLineBeforeEndBlock =
        linesBeforeEndBlock[linesBeforeEndBlock.length - 1] || "";
      const indentationMatch = lastLineBeforeEndBlock.match(/^(\s*)/);
      const indentation = indentationMatch ? indentationMatch[0] : "  "; // Default to 2 spaces

      // Add modulepreload links in the head section (JavaScript block)
      const combinedLinks = [...modulePreloadLinks, ...cssLinks];

      // Add the Django adapter script link
      const adapterStaticPath = joinUrlParts(
        djangoStaticUrlPrefix,
        djangoAdapterScriptPath,
      );
      const adapterScriptTag = `<script type="module" src="{% static '${adapterStaticPath}' %}"></script>`;

      // Include adapter script at the beginning of the head links
      const linkInjection =
        `${indentation}${adapterScriptTag}\n` +
        combinedLinks.map((link) => `${indentation}${link}`).join("\n") +
        (combinedLinks.length > 0 ? "\n" : "");

      djangoTemplateContent =
        djangoTemplateContent.substring(0, cssBlockEndIndex) +
        linkInjection +
        djangoTemplateContent.substring(cssBlockEndIndex);
      console.log(
        "Injected modulepreload links and CSS links into {% block javascript %}.",
      );
    } else {
      console.warn(
        `Warning: CSS block end marker "${cssBlockEndMarker}" not found in Django template. CSS not injected.`,
      );
    }

    // 7. Inject modified JS script tags into the svelte startup code placeholder
    const jsStartIndex = djangoTemplateContent.indexOf(jsStartMarker);
    const jsEndIndex = djangoTemplateContent.indexOf(jsEndMarker);

    if (jsStartIndex !== -1 && jsEndIndex !== -1 && jsEndIndex > jsStartIndex) {
      // Try to preserve indentation from the line of jsStartMarker
      const linesBeforeStartMarker = djangoTemplateContent
        .substring(0, jsStartIndex)
        .split("\n");
      const lineOfStartMarker =
        linesBeforeStartMarker[linesBeforeStartMarker.length - 1] || "";
      const indentationMatch = lineOfStartMarker.match(/^(\s*)/);
      const indentation = indentationMatch ? indentationMatch[0] : "    "; // Default to 4 spaces

      const jsInjection =
        jsScripts
          .map((script) => {
            // Handle special case for the SvelteKit initialization script which already has indentation and new lines
            if (script.startsWith("<script>\n {")) {
              // Only add indentation to the first line
              return `${indentation}${script.split("\n").join(`\n${indentation}`)}`;
            }
            return `${indentation}${script}`;
          })
          .join("\n") + (jsScripts.length > 0 ? "\n" : "");

      djangoTemplateContent =
        djangoTemplateContent.substring(
          0,
          jsStartIndex + jsStartMarker.length,
        ) +
        "\n" +
        jsInjection +
        (jsScripts.length > 0 ? indentation : "") +
        djangoTemplateContent.substring(jsEndIndex);
      console.log("Injected JS scripts into placeholder between markers.");
    } else {
      console.warn(
        `Warning: JS placeholder markers "${jsStartMarker}" and "${jsEndMarker}" not found or in wrong order in Django template. JS not injected.`,
      );
      console.log(`jsStartIndex: ${jsStartIndex}, jsEndIndex: ${jsEndIndex}`);
    }

    // 8. Ensure {% load static %} is at the top if not already present
    const loadStaticTag = "{% load static %}";
    if (
      !djangoTemplateContent.trim().startsWith(loadStaticTag) &&
      !djangoTemplateContent.includes(loadStaticTag)
    ) {
      const extendsRegex = /^{%\s*extends\s*.*%}\s*/;
      const match = djangoTemplateContent.match(extendsRegex);
      if (match) {
        const insertPosition = match[0].length;
        djangoTemplateContent =
          djangoTemplateContent.substring(0, insertPosition) +
          loadStaticTag +
          "\n" +
          djangoTemplateContent.substring(insertPosition);
      } else {
        djangoTemplateContent = loadStaticTag + "\n" + djangoTemplateContent;
      }
      console.log("Ensured {% load static %} tag is present.");
    }

    // 9. Write the updated Django template
    const outputDir = path.dirname(outputDjangoTemplatePath);
    await fs.mkdir(outputDir, { recursive: true });

    await fs.writeFile(
      outputDjangoTemplatePath,
      djangoTemplateContent,
      "utf-8",
    );
    console.log(
      `Successfully updated Django template at: ${outputDjangoTemplatePath}`,
    );
  } catch (error) {
    console.error("Error during Django template update process:", error);
    process.exit(1);
  }
}

main();
