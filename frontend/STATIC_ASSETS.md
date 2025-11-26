# Static Assets Configuration

This document explains how static assets are configured in the GitHubMe project, particularly how the integration between Django's static file handling and Svelte's asset loading works.

## Directory Structure

```
frontend/
├── static/         # Contains all static assets
│   ├── img/        # Image assets
│   │   ├── githubme-icon.png
│   │   └── ...
│   ├── css/        # CSS assets (if applicable)
│   └── ...
└── src/            # Svelte source code
    └── components/ # Svelte components
        └── navbar/ # Navigation components
            └── Navbar.svelte
```

## Static Asset Path Resolution

In this project, we have set up Svelte to work seamlessly with Django's static file handling.

### Configuration Details

1. **SvelteKit Configuration** (`svelte.config.js`):

   - We've configured `files.assets` to point to the `static` directory
   - Added an alias for `img` that points to `static/img`

2. **Vite Configuration** (`vite.config.ts`):
   - Added a consistent `resolve.alias` configuration for `img` pointing to `static/img`

### How It Works

When you reference images in your Svelte components using paths like:

```svelte
<img src="img/githubme-icon.png" alt="Logo" />
```

The configuration automatically maps this to `/frontend/static/img/githubme-icon.png` during development, and properly handles the path during production builds.

### Django Integration

Django has its own static file serving mechanism which typically serves files from a URL path like `/static/`. Our configuration ensures that:

1. References to images in Svelte components use the same conventions as Django
2. During development, both systems can access the same files
3. In production, the build process outputs files in a way that Django can serve them correctly

## Best Practices

1. Always reference images in Svelte components using the `img/` prefix rather than `static/img/`
2. Keep all static assets in the appropriate subdirectory of `frontend/static/`
3. If adding new types of static assets, consider adding new aliases in both config files

## Troubleshooting

If images are not loading correctly:

1. Verify the path in the component starts with `img/`
2. Check that the file exists in the corresponding `static/img/` directory
3. Ensure the configuration in both `svelte.config.js` and `vite.config.ts` is correct
4. For production issues, verify that Django's static file settings are correctly configured
