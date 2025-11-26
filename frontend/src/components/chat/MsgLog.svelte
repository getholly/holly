<script lang="ts">
  import { tick, onMount, onDestroy, createEventDispatcher } from "svelte";
  import { CheckCircleOutline } from "flowbite-svelte-icons";
  import { fade } from "svelte/transition";
  import type { Message } from "holly-api";
  import { messages } from "$lib/store/chat/chat.store";
  import MarkdownRenderer from "$components/chat/MarkdownRenderer.svelte";
  import MessageActions from "$components/chat/MessageActions.svelte";
  import CodeBlock from "$components/chat/CodeBlock.svelte";

  let msgLogEl: HTMLElement;
  let lastMessageRef: HTMLElement | null = null;
  let observer: IntersectionObserver | null = null;
  let autoScroll = true;
  export let isChatLoading = false;

  // Collection of refs to markdown rendered content for code block enhancement
  let markdownRefs: Record<number, HTMLElement | null> = {};

  const dispatch = createEventDispatcher();

  onMount(() => {
    setupIntersectionObserver();
    scrollToBottom();
  });

  onDestroy(() => {
    if (observer) {
      observer.disconnect();
    }
  });

  function setupIntersectionObserver() {
    if (!msgLogEl) return;

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // User has scrolled to the bottom
            autoScroll = true;
          } else {
            // User has scrolled up
            autoScroll = false;
          }
        });
      },
      {
        root: msgLogEl,
        threshold: 0.8,
      },
    );
  }

  $: {
    if ($messages.length > 0 && msgLogEl) {
      // Observe the last message for intersection
      if (observer && lastMessageRef) {
        observer.disconnect();
        observer.observe(lastMessageRef);
      }

      if (autoScroll) {
        scrollToBottomSmoothly();
      }
    }
  }

  export async function scrollToBottom() {
    if (!msgLogEl || msgLogEl === undefined) return;
    await tick();
    msgLogEl.scroll(0, msgLogEl.scrollHeight);
    autoScroll = true;
  }

  export async function scrollToBottomSmoothly() {
    if (!msgLogEl) return;
    await tick();

    msgLogEl.scrollTo({
      top: msgLogEl.scrollHeight,
      behavior: "smooth",
    });
    autoScroll = true;
    dispatch("scrolled-to-bottom");
  }

  // Manual scroll handling
  function handleScroll() {
    if (!msgLogEl) return;

    const isAtBottom =
      msgLogEl.scrollHeight - msgLogEl.scrollTop <= msgLogEl.clientHeight + 10;
    autoScroll = isAtBottom;
  }

  function formatDate(timestamp: string | undefined) {
    if (!timestamp) return "Missing Date";
    const date = new Date(timestamp);
    return date.toLocaleString();
  }

  function is_llm_generated(message: Message) {
    return message.role === "assistant";
  }

  // Use action directive to handle the last message reference
  function lastMessageAction(node: HTMLElement, isLast: boolean) {
    if (isLast) {
      lastMessageRef = node;
    } else if (lastMessageRef === node) {
      lastMessageRef = null;
    }

    return {
      update(newIsLast: boolean) {
        if (newIsLast) {
          lastMessageRef = node;
        } else if (lastMessageRef === node) {
          lastMessageRef = null;
        }
      },
    };
  }

  // Stub functions for message actions
  function handleCopy(index: number) {
    console.log("Message copied:", index);
  }

  function handleRetry(index: number) {
    console.log("Retry message:", index);
  }

  function handleShare(index: number) {
    console.log("Share message:", index);
  }

  function handleFeedback(index: number, event: CustomEvent) {
    console.log("Feedback for message:", index, event.detail);
  }

  // Reference action to bind markdown rendered element for code block enhancement
  function bindMarkdownRef(node: HTMLElement, index: number) {
    markdownRefs[index] = node;

    return {
      destroy() {
        markdownRefs[index] = null;
      },
    };
  }
</script>

<!-- Fixed scrolling with proper height constraints and overflow -->
<div
  class="flex flex-col h-full overflow-y-auto"
  bind:this={msgLogEl}
  on:scroll={handleScroll}
>
  <div class="pb-4">
    {#if $messages?.length}
      {#each [...$messages] as msg, index}
        <div class="p-2" use:lastMessageAction={index === $messages.length - 1}>
          <!-- AI or other user messages on the left side -->
          <div class:justify-end={msg.role === "assistant"} class="flex">
            <div
              class="bg-gray-200 rounded-lg p-4 max-w-[80%] shadow-sm"
              class:bg-theme-primary={!is_llm_generated(msg)}
              class:text-white={!is_llm_generated(msg)}
              class:dark:bg-gray-800={is_llm_generated(msg)}
              class:dark:text-gray-200={is_llm_generated(msg)}
            >
              <div class="font-semibold">
                {#if is_llm_generated(msg)}
                  AI:
                  <div use:bindMarkdownRef={index}>
                    <MarkdownRenderer
                      source={msg.content}
                      className="prose font-normal text-black dark:prose-invert max-w-none wrap-anywhere"
                    />
                  </div>
                  <!-- Add code block copy buttons -->
                  <CodeBlock element={markdownRefs[index]} />
                {:else}
                  <div use:bindMarkdownRef={index}>
                    {msg.role || "You"}:
                    <MarkdownRenderer
                      source={msg.content}
                      className="prose font-normal text-white dark:prose-invert max-w-none"
                    />
                  </div>
                  <!-- Add code block copy buttons -->
                  <CodeBlock element={markdownRefs[index]} />
                {/if}
              </div>
              <div class="text-sm mt-2 flex items-center justify-between">
                <div class="flex items-center space-x-1">
                  <span>{formatDate(msg.created_at)}</span>
                  <CheckCircleOutline size="xs" />
                </div>

                <!-- Message actions -->
                <MessageActions
                  text={msg.content}
                  role={msg.role}
                  on:copy={() => handleCopy(index)}
                  on:retry={() => handleRetry(index)}
                  on:share={() => handleShare(index)}
                  on:feedback={(e) => handleFeedback(index, e)}
                />
              </div>
            </div>
          </div>
        </div>
      {/each}
    {/if}
    {#if isChatLoading}
      <div class="w-full p-4" transition:fade>
        <div class="bg-gray-200 rounded-lg p-4 inline-block">
          <div class="flex space-x-1">
            <div
              class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
              style="animation-delay: 0s"
            ></div>
            <div
              class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
              style="animation-delay: 0.2s"
            ></div>
            <div
              class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
              style="animation-delay: 0.4s"
            ></div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>
