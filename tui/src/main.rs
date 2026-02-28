//! Holly TUI — terminal interface for the Holly AI assistant.
//!
//! Mirrors the Svelte frontend feature-set:
//!   - Login / Register / Forgot password
//!   - Dashboard (missions count, repos count, recent conversations)
//!   - Missions list + create / start / end
//!   - SSE chat (send messages, stream responses)
//!   - GitHub repositories viewer
//!   - LLMs list + API key management
//!   - Settings (server URL, theme, notifications)

use anyhow::Result;
use crossterm::{
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::prelude::*;
use std::io;
use tracing_appender::rolling::{RollingFileAppender, Rotation};

mod app;
mod config;
mod events;
mod ui;

use app::App;
use events::EventHandler;

fn setup_logging() {
    if let Some(log_dir) = dirs::data_local_dir().map(|d| d.join("holly-tui").join("logs")) {
        let _ = std::fs::create_dir_all(&log_dir);
        let file_appender = RollingFileAppender::new(Rotation::DAILY, log_dir, "holly-tui.log");
        tracing_subscriber::fmt()
            .with_writer(file_appender)
            .with_env_filter(
                tracing_subscriber::EnvFilter::from_default_env()
                    .add_directive("holly_tui=debug".parse().unwrap()),
            )
            .init();
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    setup_logging();

    // Set up terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let config = config::Config::load();
    let mut app = App::new(config);
    let mut events = EventHandler::new(200); // 200ms tick rate

    let result = run_app(&mut terminal, &mut app, &mut events).await;

    // Restore terminal
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    if let Err(e) = result {
        eprintln!("Error: {e}");
    }

    Ok(())
}

async fn run_app<B: Backend>(
    terminal: &mut Terminal<B>,
    app: &mut App,
    events: &mut EventHandler,
) -> Result<()> {
    loop {
        terminal.draw(|f| ui::draw(f, app))?;

        if let Some(event) = events.next().await {
            app.handle_event(event).await?;
        }

        if app.should_quit() {
            return Ok(());
        }
    }
}
