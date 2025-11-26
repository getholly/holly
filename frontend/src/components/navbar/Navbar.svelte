<script lang="ts">
  import { base } from "$app/paths";
  import { onMount } from "svelte";
  import {
    avatarUrl,
    userEmail,
    isAuthenticated,
  } from "$lib/store/auth/tokens.store";
  import { routes } from "$lib/routes"; // Import routes
  import { goto } from "$app/navigation";
  import DarkLightToggle from "$components/DarkLightToggle.svelte";
  import { themes } from "$lib/store/theme";

  // Use the logos from theme store
  const logo = themes.default.logo;
  const logoDark = themes.default.logoDark;

  let menuOpen = false;
  let mobileMenuOpen = false;

  function toggleUserMenu() {
    menuOpen = !menuOpen;
  }

  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }

  function closeMenus() {
    menuOpen = false;
  }

  function navigate(path) {
    goto(`${base}${path}`);
    closeMenus();
  }

  // Close menu when clicking outside
  let userMenuRef;
  let avatarRef;

  onMount(() => {
    // Add click event listener to document to detect clicks outside the menu
    const handleOutsideClick = (event) => {
      if (
        userMenuRef &&
        !userMenuRef.contains(event.target) &&
        avatarRef &&
        !avatarRef.contains(event.target)
      ) {
        menuOpen = false;
      }
    };

    document.addEventListener("click", handleOutsideClick);

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  });

  // Menu items
  const menuItems = [
    { name: "chat", href: routes.main.path }, // Use routes for consistency
    { name: "dashboard", href: "/dashboard" },
    { name: "LLMs", href: "/llms" },
    // Uncomment the line below if you want to include the Upgrade link
    // { name: 'Upgrade', href: '/subscriptions', class: 'hidden md:block' }
  ];

  // Use isAuthenticated from the store directly
</script>

<nav class="bg-theme-light-bg dark:bg-theme-dark-bg py-2.5">
  <div
    class="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto px-4"
  >
    <!-- Logo/Brand -->
    <a href="/" class="flex items-center">
      <!-- Light mode logo -->
      <img class="w-24 dark:hidden" src={logo.src} alt={logo.alt} />
      <!-- Dark mode logo -->
      <img
        class="w-24 hidden dark:block"
        src={logoDark.src}
        alt={logoDark.alt}
      />
    </a>

    <!-- Mobile menu button -->
    <div class="flex md:order-2 items-center space-x-3">
      <!-- Dark mode toggle button -->
      <DarkLightToggle version="simple" />

      <!-- User Avatar and Menu -->
      {#if isAuthenticated}
        <div class="relative">
          <!-- Avatar that toggles dropdown -->
          <button
            bind:this={avatarRef}
            class="flex items-center focus:outline-none"
            on:click|stopPropagation={toggleUserMenu}
            aria-expanded={menuOpen}
            aria-haspopup="true"
          >
            {#if $avatarUrl}
              <img
                src={$avatarUrl}
                alt="User Avatar"
                class="h-8 w-8 rounded-full object-cover border-2 border-theme-border dark:border-theme-border-dark"
              />
            {:else}
              <div
                class="h-8 w-8 rounded-full bg-theme-secondary flex items-center justify-center text-white"
              >
                {$userEmail.slice(0, 1).toUpperCase()}
              </div>
            {/if}
            <svg
              class="ml-1 h-5 w-5 text-theme-text-muted"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fill-rule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>

          <!-- Dropdown Menu -->
          {#if menuOpen}
            <div
              bind:this={userMenuRef}
              class="absolute right-0 z-50 mt-2 w-48 origin-top-right rounded-md bg-theme-surface dark:bg-theme-surface-dark py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none"
              role="menu"
              aria-orientation="vertical"
              tabindex="-1"
            >
              <!-- User info section -->
              <div
                class="px-4 py-3 border-b border-theme-border dark:border-theme-border-dark"
              >
                <p
                  class="text-sm text-theme-text-secondary dark:text-theme-text-inverse font-medium truncate"
                >
                  {$userEmail}
                </p>
              </div>

              <!-- Menu items -->
              <button
                class="w-full text-left block px-4 py-2 text-sm text-theme-text-secondary dark:text-theme-text-inverse hover:bg-theme-surface dark:hover:bg-theme-dark-bg"
                on:click={() => navigate("/settings")}
                role="menuitem"
              >
                Settings
              </button>
              <button
                class="w-full text-left block px-4 py-2 text-sm text-theme-text-secondary dark:text-theme-text-inverse hover:bg-theme-surface dark:hover:bg-theme-dark-bg"
                on:click={() => navigate("/github")}
                role="menuitem"
              >
                My Repositories
              </button>
              <button
                class="w-full text-left block px-4 py-2 text-sm text-theme-text-secondary dark:text-theme-text-inverse hover:bg-theme-surface dark:hover:bg-theme-dark-bg"
                on:click={() => navigate("/github/installations")}
                role="menuitem"
              >
                GitHub Installations
              </button>
              <hr class="border-t border-theme-border dark:border-theme-border-dark my-1" />
              <button
                class="w-full text-left block px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-theme-surface dark:hover:bg-theme-dark-bg"
                on:click={() => navigate(routes.logout.path)}
                role="menuitem"
              >
                Sign out
              </button>
            </div>
          {/if}
        </div>
      {:else}
        <!-- Login/Register buttons for non-authenticated users -->
        <div class="flex items-center md:order-2 space-x-2 rtl:space-x-reverse">
          <a
            href={routes.login.path}
            class="text-theme-text dark:text-theme-text-inverse hover:bg-theme-surface focus:ring-4 focus:ring-gray-300 font-medium rounded-lg text-sm px-4 py-2 md:px-5 md:py-2.5 dark:hover:bg-theme-surface-dark focus:outline-none dark:focus:ring-gray-800"
            >Login</a
          >
          <a
            href={routes.register.path}
            class="text-white bg-theme-primary hover:bg-theme-secondary focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 md:px-5 md:py-2.5 dark:bg-theme-secondary dark:hover:bg-theme-primary focus:outline-none dark:focus:ring-blue-800"
            >Register</a
          >
        </div>
      {/if}

      <!-- Mobile hamburger menu button -->
      <button
        class="inline-flex items-center p-2 ml-3 text-sm text-theme-text-muted rounded-lg md:hidden hover:bg-theme-surface dark:hover:bg-theme-surface-dark dark:text-theme-text-inverse"
        on:click={toggleMobileMenu}
        aria-expanded={mobileMenuOpen}
        aria-controls="mobile-menu"
      >
        <span class="sr-only">Open main menu</span>
        <svg
          class="w-6 h-6"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            fill-rule="evenodd"
            d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
            clip-rule="evenodd"
          ></path>
        </svg>
      </button>
    </div>

    <!-- Nav Links -->
    <div
      class="items-center justify-between hidden w-full md:flex md:w-auto md:order-1"
      class:hidden={!mobileMenuOpen}
      id="mobile-menu"
    >
      <ul
        class="flex flex-col p-4 md:p-0 mt-4 md:flex-row md:space-x-8 md:mt-0"
      >
        {#each menuItems as item}
          <li class={item.class || ""}>
            <a
              href={item.href}
              class="block py-2 pl-3 pr-4 text-theme-text rounded md:p-0 dark:text-theme-text-inverse hover:bg-theme-surface md:hover:bg-transparent md:hover:text-theme-primary dark:hover:bg-theme-surface-dark dark:hover:text-white md:dark:hover:bg-transparent"
              on:click={() => {
                closeMenus();
                navigate(item.href);
              }}
            >
              {item.name}
            </a>
          </li>
        {/each}

        {#if !isAuthenticated}
          <li>
            <a
              href={routes.login.path}
              class="block py-2 pl-3 pr-4 text-theme-text rounded md:p-0 dark:text-theme-text-inverse hover:bg-theme-surface md:hover:bg-transparent md:hover:text-theme-primary dark:hover:bg-theme-surface-dark dark:hover:text-white md:dark:hover:bg-transparent"
              on:click={() => {
                closeMenus();
                navigate(routes.login.path);
              }}
            >
              Login
            </a>
          </li>
          <li>
            <a
              href={routes.register.path}
              class="block py-2 pl-3 pr-4 text-theme-text rounded md:p-0 dark:text-theme-text-inverse hover:bg-theme-surface md:hover:bg-transparent md:hover:text-theme-primary dark:hover:bg-theme-surface-dark dark:hover:text-white md:dark:hover:bg-transparent"
              on:click={() => {
                closeMenus();
                navigate(routes.register.path);
              }}
            >
              Register
            </a>
          </li>
        {/if}
      </ul>
    </div>
  </div>
</nav>
