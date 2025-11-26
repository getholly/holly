<script lang="ts">
  import { dev } from "$app/environment";
  import { error } from "@sveltejs/kit";

  const errorMessage = "Internal Server Error";
  const statusCode = 500;

  if (!dev) {
    throw error(statusCode, errorMessage);
  }
</script>

<section class="bg-white dark:bg-gray-900">
  <div
    class="mx-auto max-w-screen-xl grid-cols-2 content-center gap-8 px-4 py-8 md:grid lg:px-6 lg:py-16"
  >
    <div class="self-center">
      <h1
        class="mb-4 text-2xl font-bold text-primary-600 dark:text-primary-500"
      >
        500 Internal Error
      </h1>
      <p
        class="mb-4 text-3xl font-bold tracking-tight text-gray-900 dark:text-white md:text-4xl lg:mb-10"
      >
        Whoops! That page doesn’t exist.
      </p>
      <p class="mb-4 text-gray-500 dark:text-gray-400">
        Here are some helpful links:
      </p>
      <ul class="flex items-center space-x-4 text-gray-500 dark:text-gray-400">
        <li>
          <span class="underline hover:text-gray-900 dark:hover:text-white">
            Support
          </span>
        </li>
        <li>
          <a
            href="/"
            class="underline hover:text-gray-900 dark:hover:text-white"
          >
            Home
          </a>
        </li>
      </ul>
    </div>
    <img
      class="mx-auto mb-4 hidden md:flex"
      src="https://flowbite.s3.amazonaws.com/blocks/marketing-ui/500/500.svg"
      alt="500 Server Error"
    />
  </div>
</section>
