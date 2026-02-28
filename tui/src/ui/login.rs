//! Login, Register, Forgot Password screens.

use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, LoginField};
use super::helpers::{centered_rect, status_bar, focused_block, titled_block};

pub fn render_login(f: &mut Frame, app: &App) {
    let area = f.area();
    let popup = centered_rect(60, 50, area);

    let chunks = Layout::vertical([
        Constraint::Length(3), // title
        Constraint::Length(3), // email
        Constraint::Length(3), // password
        Constraint::Length(3), // hint
        Constraint::Min(0),
        Constraint::Length(2), // status bar
    ])
    .split(popup);

    // Title
    let title = Paragraph::new(" 🌿 Holly TUI — Login ")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::NONE));
    f.render_widget(title, chunks[0]);

    // Email
    let email_block = if app.login_focused == LoginField::Email {
        focused_block(" Email ")
    } else {
        titled_block(" Email ")
    };
    let email_input = Paragraph::new(app.login_email.as_str()).block(email_block);
    f.render_widget(email_input, chunks[1]);

    // Password
    let pw_block = if app.login_focused == LoginField::Password {
        focused_block(" Password ")
    } else {
        titled_block(" Password ")
    };
    let pw_display = "*".repeat(app.login_password.len());
    let pw_input = Paragraph::new(pw_display).block(pw_block);
    f.render_widget(pw_input, chunks[2]);

    // Hints
    let hints = Paragraph::new(
        "Enter: login  Tab: switch field  Ctrl+R: register  Ctrl+F: forgot password  q: quit"
    )
    .style(Style::default().fg(Color::DarkGray))
    .alignment(Alignment::Center);
    f.render_widget(hints, chunks[3]);

    // Status bar
    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        chunks[5],
    );
}

pub fn render_register(f: &mut Frame, app: &App) {
    let area = f.area();
    let popup = centered_rect(60, 50, area);

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Min(0),
        Constraint::Length(2),
    ])
    .split(popup);

    let title = Paragraph::new(" 🌿 Holly TUI — Register ")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::NONE));
    f.render_widget(title, chunks[0]);

    let email_block = if app.login_focused == LoginField::Email {
        focused_block(" Email ")
    } else {
        titled_block(" Email ")
    };
    f.render_widget(
        Paragraph::new(app.register_email.as_str()).block(email_block),
        chunks[1],
    );

    let pw_block = if app.login_focused == LoginField::Password {
        focused_block(" Password ")
    } else {
        titled_block(" Password ")
    };
    let pw_display = "*".repeat(app.register_password.len());
    f.render_widget(
        Paragraph::new(pw_display).block(pw_block),
        chunks[2],
    );

    let hints = Paragraph::new("Enter: register  Tab: switch field  Esc: back to login")
        .style(Style::default().fg(Color::DarkGray))
        .alignment(Alignment::Center);
    f.render_widget(hints, chunks[3]);

    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        chunks[5],
    );
}

pub fn render_forgot_password(f: &mut Frame, app: &App) {
    let area = f.area();
    let popup = centered_rect(60, 40, area);

    let chunks = Layout::vertical([
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Length(3),
        Constraint::Min(0),
        Constraint::Length(2),
    ])
    .split(popup);

    let title = Paragraph::new(" 🌿 Holly TUI — Forgot Password ")
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::NONE));
    f.render_widget(title, chunks[0]);

    f.render_widget(
        Paragraph::new(app.forgot_email.as_str()).block(focused_block(" Email ")),
        chunks[1],
    );

    let hints = Paragraph::new("Enter: send reset email  Esc: back to login")
        .style(Style::default().fg(Color::DarkGray))
        .alignment(Alignment::Center);
    f.render_widget(hints, chunks[2]);

    f.render_widget(
        status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()),
        chunks[4],
    );
}
