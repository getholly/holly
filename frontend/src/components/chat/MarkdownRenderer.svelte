<script lang="ts">
  import { onMount } from "svelte";
  import MarkdownIt from "markdown-it";
  import DOMPurify from "dompurify";

  /**
   * The raw Markdown string to render.
   * @type {string}
   */
  export let source: string = "";

  /**
   * Optional className to add to the wrapper div.
   * Useful for applying styling like Tailwind's 'prose'.
   * @type {string} [className='']
   */
  export let className: string = "";

  // --- Internal State ---
  let sanitizedHtml: string = "";

  // --- Initialize Markdown-it ---
  // You can customize markdown-it options here
  const md = new MarkdownIt({
    html: false, // Disable raw HTML in Markdown source, rely on sanitizer
    breaks: true, // Convert '\n' in paragraphs into <br>
    linkify: true, // Autoconvert URL-like text to links
  });
  // Example: Add plugins like markdown-it-highlightjs for syntax highlighting
  // import hljs from 'highlight.js'; // npm install highlight.js
  // import mdHighlightjs from 'markdown-it-highlightjs'; // npm install markdown-it-highlightjs
  // md.use(mdHighlightjs, { hljs });

  // --- Reactive Rendering Logic ---
  // $: indicates this block re-runs whenever its dependencies (source) change.
  $: {
    if (typeof window !== "undefined") {
      // Ensure DOMPurify runs only in the browser
      // 1. Parse Markdown to HTML using markdown-it
      const rawHtml = md.render(source || ""); // Handle null/undefined source

      // 2. Sanitize the HTML using DOMPurify
      // You can configure DOMPurify here if needed (e.g., ALLOW_TAGS, ALLOW_ATTR)
      // See DOMPurify documentation for options.
      sanitizedHtml = DOMPurify.sanitize(rawHtml, {
        USE_PROFILES: { html: true }, // Use standard HTML profile
      });
    } else {
      // Optional: Provide a basic server-side rendering fallback or leave empty
      // Basic SSR fallback (less secure, only if absolutely necessary and source is trusted):
      // sanitizedHtml = md.render(source || '');
      sanitizedHtml = ""; // Safer default for SSR
    }
  }
</script>

<div class={className}>
  {@html sanitizedHtml}
</div>

<style>
  /* Example: Add styles if not using Tailwind prose */
  /*
    div :global(p) {
      margin-bottom: 1rem;
    }
    div :global(code) {
      background-color: #f0f0f0;
      padding: 0.1em 0.3em;
      border-radius: 4px;
    }
    div :global(pre) {
      background-color: #e8e8e8;
      padding: 0.5rem;
      border-radius: 4px;
      overflow-x: auto;
    }
    div :global(pre code) {
      background-color: transparent;
      padding: 0;
    }
    */

  /* Ensure the wrapper itself doesn't add unwanted layout shifts */
  div {
    line-height: 1.6; /* Example base line-height */
  }
</style>
