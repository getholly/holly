use ratatui::prelude::*;
use ratatui::widgets::{List, ListItem, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block};

pub fn render_wizard(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .split(content);

    let header = Paragraph::new(" 🪄 Setup Wizard")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(ratatui::widgets::Block::default().borders(ratatui::widgets::Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    let steps = vec![
        "[1] Connect GitHub repositories",
        "[2] Create a Mission",
        "[3] Configure server URL in Settings",
        "",
        "Complete these steps to get productive fast!",
        "",
        "Esc: back to Dashboard",
    ];
    let items: Vec<ListItem> = steps.iter()
        .map(|s| ListItem::new(*s).style(Style::default().fg(Color::White)))
        .collect();
    let list = List::new(items).block(titled_block(" Steps "));
    f.render_widget(list, chunks[1]);

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
