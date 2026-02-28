use ratatui::prelude::*;
use ratatui::widgets::{List, ListItem, ListState, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block, selected_style, normal_style, muted_style};

pub fn render_llms(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Ratio(1, 2),
        Constraint::Ratio(1, 2),
    ])
    .split(content);

    let header = Paragraph::new(" 🤖 LLMs & API Keys")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(ratatui::widgets::Block::default().borders(ratatui::widgets::Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    // LLMs list
    if app.llms.is_empty() {
        f.render_widget(
            Paragraph::new("No LLMs configured.")
                .style(muted_style())
                .block(titled_block(" Available LLMs ")),
            chunks[1],
        );
    } else {
        let items: Vec<ListItem> = app.llms.iter().enumerate().map(|(i, l)| {
            let provider = l.provider.as_deref().unwrap_or("—");
            let text = format!("{:<30} [{}]", l.name, provider);
            let style = if i == app.selected_llm_idx { selected_style() } else { normal_style() };
            ListItem::new(text).style(style)
        }).collect();
        let mut state = ListState::default();
        state.select(Some(app.selected_llm_idx));
        let _ = ratatui::widgets::StatefulWidget::render(
            List::new(items).block(titled_block(" Available LLMs (↑↓/jk  r: refresh  Esc: back) ")),
            chunks[1],
            f.buffer_mut(),
            &mut state,
        );
    }

    // API Keys list
    if app.api_keys.is_empty() {
        f.render_widget(
            Paragraph::new("No API keys configured.")
                .style(muted_style())
                .block(titled_block(" Your API Keys ")),
            chunks[2],
        );
    } else {
        let items: Vec<ListItem> = app.api_keys.iter().map(|k| {
            let provider = k.provider.as_deref().unwrap_or("—");
            let name = k.name.as_deref().unwrap_or("(unnamed)");
            ListItem::new(format!("{name} [{provider}]")).style(normal_style())
        }).collect();
        let list = List::new(items).block(titled_block(" Your API Keys "));
        f.render_widget(list, chunks[2]);
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
