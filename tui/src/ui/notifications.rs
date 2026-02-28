use ratatui::prelude::*;
use ratatui::widgets::{List, ListItem, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block, muted_style, normal_style};

pub fn render_notifications(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .split(content);

    let unread = app.notification_state.unread_count;
    let header = Paragraph::new(format!(" 🔔 Notifications  (unread: {unread})"))
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(ratatui::widgets::Block::default().borders(ratatui::widgets::Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    let notifs = &app.notification_state.notifications;
    if notifs.is_empty() {
        f.render_widget(
            Paragraph::new("No notifications.").style(muted_style()).block(titled_block(" Notifications ")),
            chunks[1],
        );
    } else {
        let items: Vec<ListItem> = notifs.iter().map(|n| {
            let msg = n.message.as_deref().unwrap_or("(no message)");
            let read = n.read.unwrap_or(true);
            let style = if read { muted_style() } else { Style::default().fg(Color::Yellow) };
            let prefix = if read { "  " } else { "• " };
            ListItem::new(format!("{prefix}{msg}")).style(style)
        }).collect();

        let list = List::new(items)
            .block(titled_block(" Notifications (a: mark all read  r: refresh  Esc: back) "));
        f.render_widget(list, chunks[1]);
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
