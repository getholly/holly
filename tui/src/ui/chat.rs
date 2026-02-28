use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, ChatState};
use super::helpers::{status_bar, titled_block, muted_style};

pub fn render_chat(f: &mut Frame, app: &App, conv_id: &str) {
    let area = f.area();

    // Layout: sidebar (1/3) | chat (2/3)
    let cols = Layout::horizontal([
        Constraint::Ratio(1, 3),
        Constraint::Ratio(2, 3),
    ])
    .split(area);

    // Sidebar — conversation list
    let items: Vec<ListItem> = app.conversations.iter().map(|c| {
        let title = c.title.as_deref().unwrap_or("Untitled");
        let active = c.id == conv_id;
        let style = if active {
            Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::White)
        };
        ListItem::new(title).style(style)
    }).collect();

    let sidebar = List::new(items)
        .block(titled_block(" Conversations "));
    f.render_widget(sidebar, cols[0]);

    // Main chat panel
    let chat_chunks = Layout::vertical([
        Constraint::Length(3),  // header
        Constraint::Min(0),     // messages
        Constraint::Length(3),  // input
        Constraint::Length(2),  // status
    ])
    .split(cols[1]);

    // Header
    let streaming_indicator = if app.chat_state == ChatState::Streaming { " ⏳ streaming…" } else { "" };
    let header = Paragraph::new(format!(" 💬 Chat{streaming_indicator}"))
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chat_chunks[0]);

    // Messages
    let messages_items: Vec<ListItem> = app.chat_messages.iter().map(|(role, content)| {
        let (prefix, style) = match role.as_str() {
            "user" => ("You: ", Style::default().fg(Color::Green)),
            "assistant" => ("Holly: ", Style::default().fg(Color::Cyan)),
            _ => ("System: ", muted_style()),
        };
        // Wrap long messages manually
        let display = format!("{prefix}{content}");
        ListItem::new(display).style(style)
    }).collect();

    let messages_list = List::new(messages_items)
        .block(titled_block(" Messages "));
    f.render_widget(messages_list, chat_chunks[1]);

    // Input
    let input_style = if app.chat_state == ChatState::Streaming {
        Style::default().fg(Color::DarkGray)
    } else {
        Style::default().fg(Color::White)
    };
    let input = Paragraph::new(app.chat_input.as_str())
        .style(input_style)
        .block(Block::default()
            .title(" Message (Enter: send  Esc: dashboard) ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Blue)));
    f.render_widget(input, chat_chunks[2]);

    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        chat_chunks[3],
    );
}
