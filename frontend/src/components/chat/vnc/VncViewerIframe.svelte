<script lang="ts">
  let noVncBaseUrl: string = "https://localhost:6901";
  let targetVncHost: string = "localhost"; // Host for noVNC to connect to (usually localhost from its perspective)
  let targetVncPort: number = 6901; // Port for noVNC to connect to (e.g., 5901, 6901 from docker-compose)
  let vncUsername: string = "kasm-user";
  let vncPassword: string = "vncpassword"; // The actual VNC server password

  let iframeSrc: string | null = null;
  let showConnectionSettings: boolean = true;
  let connectionError: string | null = null;

  function connectToVnc() {
    connectionError = null;
    noVncBaseUrl = `https://${targetVncHost}:${targetVncPort}`;
    if (!noVncBaseUrl || !targetVncHost || !targetVncPort) {
      connectionError =
        "Please fill in all required fields for noVNC connection.";
      alert(connectionError);
      return;
    }
    // Construct the path for noVNC, which includes parameters for the target VNC server
    const params = new URLSearchParams({
      host: targetVncHost,
      port: targetVncPort.toString(),
      // Only add password to the URL if it's provided.
      // Some noVNC setups might not require it in the URL if they prompt.
      ...(vncPassword && { password: vncPassword }),
      username: vncUsername,
      autoconnect: "true",
      resize: "remote", // or 'scale', 'local'
      // Other useful params: view_only, show_dot
    });
    iframeSrc = `${noVncBaseUrl}?${params.toString()}`;
    showConnectionSettings = false;
    console.log(`Connecting iframe to: ${iframeSrc}`);
  }

  function disconnect() {
    iframeSrc = null;
    showConnectionSettings = true;
    connectionError = null;
  }

  // Optional: Attempt to autoconnect if defaults are plausible
  // onMount(() => {
  //   if (noVncBaseUrl.includes('localhost') || noVncBaseUrl.includes('127.0.0.1')) {
  //     // connectToVnc(); // Uncomment to autoconnect on mount
  //   }
  // });
</script>

<div class="vnc-iframe-container p-4 rounded-lg dark:text-gray-100">
  {#if showConnectionSettings}
    <div class="settings-panel mb-4 rounded">
      <h2 class="text-xl font-semibold mb-3 text-gray-700 dark:text-gray-200">
        VNC Connection (via noVNC Iframe)
      </h2>
      {#if connectionError}
        <div
          class="mb-3 p-3 bg-red-100 text-red-700 border border-red-300 rounded-md"
        >
          {connectionError}
        </div>
      {/if}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label for="vncUsername" class="block text-sm font-medium mb-1"
            >Username:</label
          >
          <input
            type="text"
            id="vncUsername"
            bind:value={vncUsername}
            class="dark:bg-gray-900 w-full p-2 border border-gray-300 dark:border-gray-800 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="http://localhost:6080/vnc.html"
          />
        </div>
        <div>
          <label for="targetVncHost" class="block text-sm font-medium mb-1"
            >Hostname:</label
          >
          <input
            type="text"
            id="targetVncHost"
            bind:value={targetVncHost}
            class="w-full p-2 border border-gray-300 dark:bg-gray-900 dark:border-gray-800 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="localhost"
          />
        </div>
        <div>
          <label
            for="targetVncPort"
            class="block text-sm font-medium text-gray-700 mb-1">Port:</label
          >
          <input
            type="number"
            id="targetVncPort"
            bind:value={targetVncPort}
            class="w-full p-2 border border-gray-300 rounded-md dark:bg-gray-900 dark:border-gray-800 shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="5901"
          />
        </div>
        <div>
          <label
            for="vncPassword"
            class="block text-sm font-medium text-gray-700 mb-1"
            >VNC Password:</label
          >
          <input
            type="password"
            id="vncPassword"
            bind:value={vncPassword}
            class="w-full p-2 border border-gray-300 dark:bg-gray-900 dark:border-gray-800 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            placeholder="VNC Server Password"
          />
        </div>
      </div>
      <button
        on:click={connectToVnc}
        class="mt-12 w-full bg-theme-primary hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 transition duration-150 ease-in-out"
      >
        Connect
      </button>
    </div>
  {/if}

  {#if iframeSrc}
    <div class="iframe-panel">
      <div class="flex justify-between items-center mb-2">
        <p class="text-sm text-gray-600">
          VNC session active. Target: <code
            >{targetVncHost}:{targetVncPort}</code
          >
          via noVNC at <code>{noVncBaseUrl}</code>
        </p>
        <button
          on:click={disconnect}
          class="bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 transition duration-150 ease-in-out"
        >
          Disconnect
        </button>
      </div>
      <iframe
        src={iframeSrc}
        title="VNC Session via noVNC"
        class="w-full h-[600px] border border-gray-300 rounded-md shadow-inner"
        allowfullscreen
      ></iframe>
    </div>
  {:else if !showConnectionSettings}
    <div class="text-center p-5">
      <p class="text-gray-500">Not connected. Configure and click "Connect".</p>
    </div>
  {/if}
</div>

<style>
  /* Add any additional component-specific styles here if Tailwind isn't enough */
  .vnc-iframe-container {
    min-height: 400px; /* Ensure container has some height */
  }
  iframe {
    background-color: #f0f0f0; /* Placeholder background before content loads */
  }
</style>
