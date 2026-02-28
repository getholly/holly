//! Event handling — keyboard input + async tick timer.

use crossterm::event::{self, Event as CrosstermEvent, KeyCode, KeyEvent, KeyModifiers};
use std::time::Duration;
use tokio::sync::mpsc;
use tokio::time;

/// Events the TUI reacts to.
#[derive(Debug, Clone)]
pub enum AppEvent {
    Key(KeyEvent),
    Tick,
    Resize(u16, u16),
}

pub struct EventHandler {
    rx: mpsc::UnboundedReceiver<AppEvent>,
}

impl EventHandler {
    pub fn new(tick_rate_ms: u64) -> Self {
        let (tx, rx) = mpsc::unbounded_channel();
        let tx2 = tx.clone();

        // Spawn keyboard reader
        tokio::task::spawn_blocking(move || {
            loop {
                if event::poll(Duration::from_millis(50)).unwrap_or(false) {
                    if let Ok(ev) = event::read() {
                        match ev {
                            CrosstermEvent::Key(k) => { let _ = tx.send(AppEvent::Key(k)); }
                            CrosstermEvent::Resize(w, h) => { let _ = tx.send(AppEvent::Resize(w, h)); }
                            _ => {}
                        }
                    }
                }
            }
        });

        // Spawn tick timer
        tokio::spawn(async move {
            let mut interval = time::interval(Duration::from_millis(tick_rate_ms));
            loop {
                interval.tick().await;
                let _ = tx2.send(AppEvent::Tick);
            }
        });

        Self { rx }
    }

    pub async fn next(&mut self) -> Option<AppEvent> {
        self.rx.recv().await
    }
}

/// Helper: check if a key event is Ctrl+C or 'q' (global quit).
pub fn is_quit(key: &KeyEvent) -> bool {
    matches!(
        key,
        KeyEvent { code: KeyCode::Char('c'), modifiers: KeyModifiers::CONTROL, .. }
        | KeyEvent { code: KeyCode::Char('q'), modifiers: KeyModifiers::NONE, .. }
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use crossterm::event::{KeyCode, KeyEvent, KeyModifiers, KeyEventKind, KeyEventState};

    fn key(code: KeyCode, mods: KeyModifiers) -> KeyEvent {
        KeyEvent { code, modifiers: mods, kind: KeyEventKind::Press, state: KeyEventState::NONE }
    }

    #[test]
    fn ctrl_c_is_quit() {
        let k = key(KeyCode::Char('c'), KeyModifiers::CONTROL);
        assert!(is_quit(&k));
    }

    #[test]
    fn q_is_quit() {
        let k = key(KeyCode::Char('q'), KeyModifiers::NONE);
        assert!(is_quit(&k));
    }

    #[test]
    fn enter_is_not_quit() {
        let k = key(KeyCode::Enter, KeyModifiers::NONE);
        assert!(!is_quit(&k));
    }

    #[test]
    fn ctrl_q_is_not_quit() {
        // Only bare 'q' quits (not ctrl+q)
        let k = key(KeyCode::Char('q'), KeyModifiers::CONTROL);
        assert!(!is_quit(&k));
    }
}
