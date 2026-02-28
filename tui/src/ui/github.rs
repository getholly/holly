use ratatui::prelude::*;
use ratatui::widgets::{List, ListItem, ListState, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::App;
use super::helpers::{page_layout, status_bar, titled_block, selected_style, normal_style, muted_style};

pub fn render_github(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .split(content);

    let header = Paragraph::new(" 🐙 GitHub Repositories")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(ratatui::widgets::Block::default().borders(ratatui::widgets::Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    if app.repositories.is_empty() {
        let placeholder = Paragraph::new("No repositories connected. Connect GitHub in Settings.")
            .style(muted_style())
            .block(titled_block(" Repositories "));
        f.render_widget(placeholder, chunks[1]);
    } else {
        let items: Vec<ListItem> = app.repositories.iter().enumerate().map(|(i, r)| {
            let name = r.full_name.as_deref().or(r.name.as_deref()).unwrap_or("unknown");
            let private = r.private.map(|p| if p { "🔒" } else { "🔓" }).unwrap_or("");
            let branch = r.default_branch.as_deref().unwrap_or("main");
            let text = format!("{private} {name}  [{branch}]");
            let style = if i == app.selected_repo_idx { selected_style() } else { normal_style() };
            ListItem::new(text).style(style)
        }).collect();

        let mut state = ListState::default();
        state.select(Some(app.selected_repo_idx));
        let _ = ratatui::widgets::StatefulWidget::render(
            List::new(items)
                .block(titled_block(" Repositories (↑↓/jk: navigate  r: refresh  Esc: back) ")),
            chunks[1],
            f.buffer_mut(),
            &mut state,
        );
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
