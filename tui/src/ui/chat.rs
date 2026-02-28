use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, ChatPhase};
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
    let items: Vec<ListItem> = app.chat.conversations.iter().map(|c| {
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

    let streaming = app.chat.phase == ChatPhase::Streaming;

    // Main chat panel — extra row for live streaming buffer when active
    let chat_chunks = if streaming {
        Layout::vertical([
            Constraint::Length(3),  // header
            Constraint::Min(0),     // completed messages
            Constraint::Length(5),  // streaming buffer
            Constraint::Length(3),  // input
            Constraint::Length(2),  // status
        ]).split(cols[1])
    } else {
        Layout::vertical([
            Constraint::Length(3),  // header
            Constraint::Min(0),     // messages
            Constraint::Length(0),  // (hidden streaming buffer)
            Constraint::Length(3),  // input
            Constraint::Length(2),  // status
        ]).split(cols[1])
    };

    // Header
    let streaming_indicator = if streaming { " ⏳ streaming…" } else { "" };
    let header = Paragraph::new(format!(" 💬 Chat{streaming_indicator}"))
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chat_chunks[0]);

    // Completed messages
    let messages_items: Vec<ListItem> = app.chat.messages.iter().map(|(role, content)| {
        let (prefix, style) = match role.as_str() {
            "user" => ("You: ", Style::default().fg(Color::Green)),
            "assistant" => ("Holly: ", Style::default().fg(Color::Cyan)),
            _ => ("System: ", muted_style()),
        };
        let display = format!("{prefix}{content}");
        ListItem::new(display).style(style)
    }).collect();

    let messages_list = List::new(messages_items)
        .block(titled_block(" Messages "));
    f.render_widget(messages_list, chat_chunks[1]);

    // Live streaming buffer — visible only while streaming
    if streaming && !chat_chunks[2].is_empty() {
        let buf_text = format!("Holly: {}", app.chat.streaming_buffer);
        let buf = Paragraph::new(buf_text)
            .style(Style::default().fg(Color::Cyan))
            .wrap(Wrap { trim: false })
            .block(Block::default()
                .title(" Streaming… ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Yellow)));
        f.render_widget(buf, chat_chunks[2]);
    }

    // Input
    let input_style = if streaming {
        Style::default().fg(Color::DarkGray)
    } else {
        Style::default().fg(Color::White)
    };
    let input = Paragraph::new(app.chat.input.as_str())
        .style(input_style)
        .block(Block::default()
            .title(" Message (Enter: send  Esc: dashboard) ")
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Blue)));
    f.render_widget(input, chat_chunks[3]);

    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        chat_chunks[4],
    );
}
