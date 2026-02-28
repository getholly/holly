use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block, muted_style};

pub fn render_dashboard(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());
    let chunks = Layout::vertical([
        Constraint::Length(3), Constraint::Length(5),
        Constraint::Length(9), Constraint::Min(0),
    ]).split(content);

    let email = if app.client.is_authenticated() {
        format!(" 🌿 Holly — Welcome, {}", app.client.current_email())
    } else {
        " 🌿 Holly — Dashboard".into()
    };
    f.render_widget(
        Paragraph::new(email)
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
            .block(Block::default().borders(Borders::BOTTOM)),
        chunks[0],
    );

    // Stats row
    let stats_chunks = Layout::horizontal([
        Constraint::Ratio(1, 3), Constraint::Ratio(1, 3), Constraint::Ratio(1, 3),
    ]).split(chunks[1]);

    let stat_items = [
        (" Missions ",      app.dashboard.missions_count),
        (" Repositories ",  app.dashboard.repos_count),
        (" Conversations ", app.dashboard.conversations_count),
    ];
    for (i, (label, count)) in stat_items.iter().enumerate() {
        let block = titled_block(label);
        f.render_widget(
            Paragraph::new(format!("{count}"))
                .style(Style::default().fg(Color::White).add_modifier(Modifier::BOLD))
                .block(block),
            stats_chunks[i],
        );
    }

    // Quick actions
    let notif_badge = if app.notifications.unread_count > 0 {
        format!(" ({})", app.notifications.unread_count)
    } else {
        String::new()
    };
    let actions = [
        "[1/c] Chat", "[2/g] GitHub", "[3/m] Missions",
        "[4/l] LLMs", "[5/s] Settings",
    ];
    let mut items: Vec<ListItem> = actions.iter()
        .map(|a| ListItem::new(*a).style(Style::default().fg(Color::White)))
        .collect();
    items.push(ListItem::new(format!("[n]   Notifications{notif_badge}"))
        .style(Style::default().fg(Color::White)));
    items.push(ListItem::new("[w]   Wizard").style(Style::default().fg(Color::White)));
    items.push(ListItem::new("[q]   Quit").style(muted_style()));
    f.render_widget(List::new(items).block(titled_block(" Quick Actions ")), chunks[2]);

    // Recent conversations
    if app.dashboard.recent_conversations.is_empty() {
        f.render_widget(
            Paragraph::new("No recent conversations. Press [1] to start chatting!")
                .style(muted_style()).block(titled_block(" Recent Conversations ")),
            chunks[3],
        );
    } else {
        let conv_items: Vec<ListItem> = app.dashboard.recent_conversations.iter()
            .map(|c| {
                let title   = c.title.as_deref().unwrap_or("Untitled");
                let updated = c.updated_at.as_deref().unwrap_or("—");
                ListItem::new(format!("{title}  ({updated})"))
                    .style(Style::default().fg(Color::White))
            })
            .collect();
        f.render_widget(
            List::new(conv_items).block(titled_block(" Recent Conversations ")),
            chunks[3],
        );
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
