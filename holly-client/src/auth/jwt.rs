/// JWT expiry helpers — no signature verification needed (server validates).
/// We only decode the `exp` claim to proactively refresh before a 401.

use chrono::Utc;
use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};

/// Decode a JWT payload (middle section) and return whether its `exp` has passed.
/// Returns `true` (expired) when the token is empty, malformed, or past its `exp`.
pub fn is_token_expired(token: &str) -> bool {
    if token.is_empty() {
        return true;
    }
    parse_exp(token)
        .map(|exp| Utc::now().timestamp() >= exp)
        .unwrap_or(true) // treat parse failures as expired → trigger refresh
}

fn parse_exp(token: &str) -> Option<i64> {
    let parts: Vec<&str> = token.splitn(3, '.').collect();
    if parts.len() != 3 {
        return None;
    }
    let payload = URL_SAFE_NO_PAD.decode(parts[1]).ok()?;
    let json: serde_json::Value = serde_json::from_slice(&payload).ok()?;
    json["exp"].as_i64()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_token_is_expired() {
        assert!(is_token_expired(""));
    }

    #[test]
    fn malformed_token_is_expired() {
        assert!(is_token_expired("not.a.jwt"));
    }

    #[test]
    fn future_exp_is_not_expired() {
        // Build a synthetic JWT with exp = year 2099
        let header = URL_SAFE_NO_PAD.encode(r#"{"alg":"HS256","typ":"JWT"}"#);
        let payload = URL_SAFE_NO_PAD.encode(r#"{"sub":"user","exp":4102444800}"#); // 2100-01-01
        let token = format!("{}.{}.fakesig", header, payload);
        assert!(!is_token_expired(&token));
    }

    #[test]
    fn past_exp_is_expired() {
        let header = URL_SAFE_NO_PAD.encode(r#"{"alg":"HS256","typ":"JWT"}"#);
        let payload = URL_SAFE_NO_PAD.encode(r#"{"sub":"user","exp":1}"#); // 1970-01-01
        let token = format!("{}.{}.fakesig", header, payload);
        assert!(is_token_expired(&token));
    }
}
