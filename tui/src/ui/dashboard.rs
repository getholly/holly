//! Dashboard screen — mirrors the Svelte dashboard page.

use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block, muted_style};

pub fn render_dashboard(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),  // header
        Constraint::Length(5),  // stats row
        Constraint::Length(9),  // quick actions
        Constraint::Min(0),     // recent conversations
    ])
    .split(content);

    // Header
    let email = if app.client.is_authenticated() {
        format!(" 🌿 Holly — Welcome, {}", app.client.current_email())
    } else {
        " 🌿 Holly — Dashboard".into()
    };
    let header = Paragraph::new(email)
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    // Stats row
    let stats_chunks = Layout::horizontal([
        Constraint::Ratio(1, 3),
        Constraint::Ratio(1, 3),
        Constraint::Ratio(1, 3),
    ])
    .split(chunks[1]);

    let stat_items = [
        (" Missions ", app.missions_count),
        (" Repositories ", app.repos_count),
        (" Conversations ", app.conversations_count),
    ];
    for (i, (label, count)) in stat_items.iter().enumerate() {
        let block = titled_block(label);
        let stat = Paragraph::new(format!("{count}"))
            .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD))
            .block(block);
        f.render_widget(stat, stats_chunks[i]);
    }

    // Quick actions
    let actions_block = titled_block(" Quick Actions ");
    let notif_badge = if app.notification_state.unread_count > 0 {
        format!(" ({})", app.notification_state.unread_count)
    } else {
        String::new()
    };
    let actions = vec![
        format!("[1/c] Chat"),
        format!("[2/g] GitHub"),
        format!("[3/m] Missions"),
        format!("[4/l] LLMs"),
        format!("[5/s] Settings"),
        format!("[n]   Notifications{notif_badge}"),
        format!("[w]   Wizard"),
        format!("[q]   Quit"),
    ];
    let items: Vec<ListItem> = actions
        .iter()
        .map(|a| ListItem::new(a.as_str()).style(Style::default().fg(Color::White)))
        .collect();
    let list = List::new(items).block(actions_block);
    f.render_widget(list, chunks[2]);

    // Recent conversations
    if app.recent_conversations.is_empty() {
        let placeholder = Paragraph::new("No recent conversations. Press [1] to start chatting!")
            .style(muted_style())
            .block(titled_block(" Recent Conversations "));
        f.render_widget(placeholder, chunks[3]);
    } else {
        let items: Vec<ListItem> = app
            .recent_conversations
            .iter()
            .map(|c| {
                let title = c.title.as_deref().unwrap_or("Untitled");
                let updated = c.updated_at.as_deref().unwrap_or("—");
                ListItem::new(format!("{title}  ({updated})"))
                    .style(Style::default().fg(Color::White))
            })
            .collect();
        let list = List::new(items).block(titled_block(" Recent Conversations "));
        f.render_widget(list, chunks[3]);
    }

    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        status,
    );
}
