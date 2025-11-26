class StreamingRequest {
  private abortController: AbortController | null = null;

  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: ((error: any) => void) | null = null;
  onopen: (() => void) | null = null;

  async connect(
    url: string,
    options: {
      method?: string;
      body?: string;
      headers?: Record<string, string>;
      credentials?: RequestCredentials;
    },
  ) {
    this.abortController = new AbortController();

    try {
      const response = await fetch(url, {
        ...options,
        signal: this.abortController.signal,
        cache: "no-cache",
        keepalive: true,
        headers: {
          Accept: "text/event-stream",
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      this.onopen?.();

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body reader available");

      const decoder = new TextDecoder();

      while (!this.abortController.signal.aborted) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            this.onmessage?.({ data });
          }
        }
      }
    } catch (error) {
      this.onerror?.(error);
    }
  }

  close() {
    this.abortController?.abort();
  }
}

export default StreamingRequest;

// Usage:
/*
const streamingRequest = new StreamingRequest()
streamingRequest.onmessage = (event) => {
    console.log('Received:', event.data)
}
streamingRequest.onerror = (error) => {
    console.error('Streaming error:', error)
}

await streamingRequest.connect(url, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(messageData)
})

 */
