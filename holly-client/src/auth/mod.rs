/// JWT token store with automatic refresh support.
///
/// Wraps access/refresh tokens and exposes helpers for:
/// - Storing tokens after login
/// - Checking if the access token is expired (by decoding the JWT exp claim)
/// - Refreshing via `/_api/token/refresh` when a 401 is detected

mod token_store;
mod jwt;

pub use token_store::TokenStore;
pub use jwt::is_token_expired;
