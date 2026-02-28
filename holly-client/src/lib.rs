/// Holly API Client Library
///
/// Provides a fully typed API client for the Holly backend,
/// wrapped in a service layer that automatically handles JWT auth and token refresh.
///
/// # Quick Start
/// ```rust,no_run
/// use holly_client::HollyClient;
///
/// #[tokio::main]
/// async fn main() -> anyhow::Result<()> {
///     let client = HollyClient::new("http://localhost:8000");
///     client.auth().login("user@example.com", "password").await?;
///     let missions = client.missions().list().await?;
///     println!("Missions: {}", missions.len());
///     Ok(())
/// }
/// ```

pub mod auth;
pub mod models;
pub mod api;
pub mod services;
pub mod error;

pub use auth::TokenStore;
pub use error::{HollyError, Result};
pub use services::HollyClient;
