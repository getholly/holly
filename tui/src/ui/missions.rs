use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, List, ListItem, ListState, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, MissionAction};
use super::helpers::{page_layout, status_bar, titled_block, selected_style, normal_style, muted_style, centered_rect};

pub fn render_missions(f: &mut Frame, app: &App) {
    let (content, status) = page_layout(f.area());

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Min(0),
    ])
    .split(content);

    let header = Paragraph::new(" 🎯 Missions")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    if app.missions.is_empty() {
        let placeholder = Paragraph::new("No missions yet. Press [n] to create one.")
            .style(muted_style())
            .block(titled_block(" Missions "));
        f.render_widget(placeholder, chunks[1]);
    } else {
        let items: Vec<ListItem> = app.missions.iter().enumerate().map(|(i, m)| {
            let state_str = m.state.as_ref()
                .map(|s| format!("{:?}", s))
                .unwrap_or_else(|| "—".into());
            let text = format!("{:<40} [{}]", m.name, state_str);
            let style = if i == app.selected_mission_idx { selected_style() } else { normal_style() };
            ListItem::new(text).style(style)
        }).collect();

        let mut state = ListState::default();
        state.select(Some(app.selected_mission_idx));
        let list = ratatui::widgets::StatefulWidget::render(
            List::new(items)
                .block(titled_block(" Missions (↑↓/jk: navigate  Enter: open  n: new  r: refresh  Esc: back) ")),
            chunks[1],
            f.buffer_mut(),
            &mut state,
        );
        let _ = list;
    }

    // New mission input popup
    if app.mission_action == MissionAction::Creating {
        let popup = centered_rect(50, 20, f.area());
        let input = Paragraph::new(app.new_mission_name.as_str())
            .block(Block::default()
                .title(" New Mission Name (Enter: save  Esc: cancel) ")
                .borders(Borders::ALL)
                .border_style(Style::default().fg(Color::Cyan)));
        f.render_widget(ratatui::widgets::Clear, popup);
        f.render_widget(input, popup);
    }

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}

pub fn render_mission_detail(f: &mut Frame, app: &App, id: &str) {
    let (content, status) = page_layout(f.area());

    let Some(mission) = &app.current_mission else {
        f.render_widget(Paragraph::new("Loading…"), content);
        return;
    };

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Length(6),
        Constraint::Min(0),
    ])
    .split(content);

    let header = Paragraph::new(format!(" 🎯 Mission: {}", mission.name))
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .block(Block::default().borders(Borders::BOTTOM));
    f.render_widget(header, chunks[0]);

    let state = mission.state.as_ref().map(|s| format!("{:?}", s)).unwrap_or("—".into());
    let desc = mission.description.as_deref().unwrap_or("—");
    let info = format!(
        "ID: {}\nState: {}\nDescription: {}\nRepositories: {}  Tools: {}  Knowledge: {}",
        mission.id, state, desc,
        mission.repositories.len(),
        mission.tools.len(),
        mission.knowledge.len(),
    );
    let info_widget = Paragraph::new(info).block(titled_block(" Details "));
    f.render_widget(info_widget, chunks[1]);

    let hints = Paragraph::new(
        "[s] Start mission  [e] End mission  [c] New conversation  Esc: back"
    )
    .style(Style::default().fg(Color::DarkGray))
    .block(titled_block(" Actions "));
    f.render_widget(hints, chunks[2]);

    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), status);
}
