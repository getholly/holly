use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, SettingsTab};
use super::helpers::{page_layout, status_bar, render_tabs, titled_block, focused_block};

pub fn render_settings(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),  // header
        Constraint::Length(3),  // tabs
        Constraint::Min(0),     // tab content
    ])
    .split(content);

    let header = Paragraph::new(" ⚙️  Settings")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    let tab_idx = match app.settings_tab {
        SettingsTab::General => 0,
        SettingsTab::Llm => 1,
        SettingsTab::Github => 2,
        SettingsTab::About => 3,
    };
    let tabs = render_tabs(vec!["General", "LLM", "GitHub", "About"], tab_idx);
    f.render_widget(tabs, chunks[1]);

    match app.settings_tab {
        SettingsTab::General => render_general_tab(f, app, chunks[2]),
        SettingsTab::Llm => render_llm_tab(f, app, chunks[2]),
        SettingsTab::Github => render_github_tab(f, app, chunks[2]),
        SettingsTab::About => render_about_tab(f, chunks[2]),
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}

fn render_general_tab(f: &mut Frame, app: &App, area: Rect) {
    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .split(area);

    let url_input = Paragraph::new(app.settings_server_url.as_str())
        .block(focused_block(" Server URL (Enter: save) "));
    f.render_widget(url_input, chunks[0]);

    let hints = Paragraph::new("Tab: switch tabs  Esc: back")
        .style(Style::default().fg(Color::DarkGray));
    f.render_widget(hints, chunks[1]);
}

fn render_llm_tab(f: &mut Frame, app: &App, area: Rect) {
    let info = Paragraph::new(
        format!(
            "Configured LLMs: {}\nAPI Keys: {}\n\nGo to [l] LLMs screen to manage.",
            app.llms.len(), app.api_keys.len()
        )
    )
    .block(titled_block(" LLM Settings "));
    f.render_widget(info, area);
}

fn render_github_tab(f: &mut Frame, app: &App, area: Rect) {
    let info = Paragraph::new(
        format!(
            "Connected repositories: {}\n\nGo to [g] GitHub screen to manage.",
            app.repositories.len()
        )
    )
    .block(titled_block(" GitHub Settings "));
    f.render_widget(info, area);
}

fn render_about_tab(f: &mut Frame, area: Rect) {
    let info = Paragraph::new(concat!(
        "Holly TUI v0.1.0\n",
        "A terminal interface for the Holly AI assistant.\n\n",
        "Built with Ratatui + holly-client (Rust)\n",
        "Mirrors all features of the Svelte web frontend.\n\n",
        "https://github.com/yourusername/holly",
    ))
    .block(titled_block(" About "));
    f.render_widget(info, area);
}
