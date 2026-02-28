/// Server-Sent Events (SSE) streaming support.
/// Used for `/missions/sse/start/{id}` and `/conversations/sse/send_message/{id}`.

use futures_util::StreamExt;
use reqwest::Client;
use std::pin::Pin;

use crate::error::{HollyError, Result};
use crate::models::SseEvent;

/// An async stream of SSE events from the Holly backend.
pub struct SseStream {
    inner: Pin<Box<dyn futures_util::Stream<Item = Result<SseEvent>> + Send>>,
}

impl SseStream {
    /// Connect to an SSE endpoint and return a stream of parsed events.
    /// The token is passed as a query parameter because `EventSource` doesn't
    /// support custom headers (matching the frontend pattern).
    pub async fn connect(http: &Client, url: &str) -> Result<Self> {
        let resp = http
            .get(url)
            .header("Accept", "text/event-stream")
            .header("Cache-Control", "no-cache")
            .send()
            .await
            .map_err(HollyError::Http)?;

        if !resp.status().is_success() {
            let status = resp.status().as_u16();
            let msg = resp.text().await.unwrap_or_default();
            return Err(HollyError::Api { status, message: msg });
        }

        let byte_stream = resp.bytes_stream();
        let event_stream = byte_stream.flat_map(|chunk_result| {
            let events = match chunk_result {
                Err(e) => vec![Err(HollyError::Http(e))],
                Ok(bytes) => parse_sse_chunk(&bytes),
            };
            futures_util::stream::iter(events)
        });

        Ok(Self { inner: Box::pin(event_stream) })
    }
}

impl futures_util::Stream for SseStream {
    type Item = Result<SseEvent>;

    fn poll_next(
        mut self: Pin<&mut Self>,
        cx: &mut std::task::Context<'_>,
    ) -> std::task::Poll<Option<Self::Item>> {
        self.inner.as_mut().poll_next(cx)
    }
}

/// Parse raw SSE bytes into zero or more `SseEvent`s.
/// SSE format: `data: {...}\n\n`
fn parse_sse_chunk(bytes: &[u8]) -> Vec<Result<SseEvent>> {
    let text = match std::str::from_utf8(bytes) {
        Ok(t) => t,
        Err(_) => return vec![Err(HollyError::Sse("Invalid UTF-8 in SSE stream".into()))],
    };

    text.split("\n\n")
        .filter(|block| !block.trim().is_empty())
        .filter_map(|block| {
            // Check for [DONE] sentinel
            if block.trim() == "data: [DONE]" {
                return None; // signals end of stream
            }

            let data = block
                .lines()
                .filter_map(|line| line.strip_prefix("data: "))
                .collect::<Vec<_>>()
                .join("");

            if data.is_empty() {
                return None;
            }

            Some(
                serde_json::from_str::<SseEvent>(&data)
                    .map_err(|e| HollyError::Serde(e)),
            )
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_single_event() {
        let chunk = b"data: {\"token\":\"Hello\"}\n\n";
        let events = parse_sse_chunk(chunk);
        assert_eq!(events.len(), 1);
        let ev = events[0].as_ref().unwrap();
        assert_eq!(ev.token, Some("Hello".into()));
    }

    #[test]
    fn parse_done_sentinel_returns_empty() {
        let chunk = b"data: [DONE]\n\n";
        let events = parse_sse_chunk(chunk);
        assert!(events.is_empty());
    }

    #[test]
    fn parse_multiple_events() {
        let chunk = b"data: {\"token\":\"Hi\"}\n\ndata: {\"token\":\" there\"}\n\n";
        let events = parse_sse_chunk(chunk);
        assert_eq!(events.len(), 2);
    }

    #[test]
    fn parse_empty_chunk() {
        let events = parse_sse_chunk(b"");
        assert!(events.is_empty());
    }

    #[test]
    fn parse_invalid_json_returns_error() {
        let chunk = b"data: not-json\n\n";
        let events = parse_sse_chunk(chunk);
        assert_eq!(events.len(), 1);
        assert!(events[0].is_err());
    }
}
