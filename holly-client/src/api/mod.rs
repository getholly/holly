/// Low-level HTTP client wrapping reqwest with:
/// - Automatic Bearer token injection
/// - 401 detection → token refresh → retry (once)
/// - JSON serialization/deserialization via serde_json

mod client;
mod sse;

pub use client::ApiClient;
pub use sse::SseStream;
