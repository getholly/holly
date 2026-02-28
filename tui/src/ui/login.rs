use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph};
use ratatui::style::{Color, Modifier, Style};

use crate::app::state::{App, LoginField};
use super::helpers::{centered_rect, status_bar, focused_block, titled_block};

pub fn render_login(f: &mut Frame, app: &App) {
    let popup = centered_rect(60, 50, f.area());
    let chunks = Layout::vertical([
        Constraint::Length(3), Constraint::Length(3), Constraint::Length(3),
        Constraint::Length(3), Constraint::Min(0),    Constraint::Length(2),
    ]).split(popup);

    f.render_widget(
        Paragraph::new(" 🌿 Holly TUI — Login ")
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::NONE)),
        chunks[0],
    );

    let email_block = if app.auth.focused == LoginField::Email { focused_block(" Email ") }
                      else { titled_block(" Email ") };
    f.render_widget(Paragraph::new(app.auth.email.as_str()).block(email_block), chunks[1]);

    let pw_block = if app.auth.focused == LoginField::Password { focused_block(" Password ") }
                   else { titled_block(" Password ") };
    f.render_widget(
        Paragraph::new("*".repeat(app.auth.password.len())).block(pw_block),
        chunks[2],
    );

    f.render_widget(
        Paragraph::new("Enter: login  Tab: switch field  Ctrl+R: register  Ctrl+F: forgot  q: quit")
            .style(Style::default().fg(Color::DarkGray)).alignment(Alignment::Center),
        chunks[3],
    );
    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), chunks[5]);
}

pub fn render_register(f: &mut Frame, app: &App) {
    let popup = centered_rect(60, 50, f.area());
    let chunks = Layout::vertical([
        Constraint::Length(3), Constraint::Length(3), Constraint::Length(3),
        Constraint::Length(3), Constraint::Min(0),    Constraint::Length(2),
    ]).split(popup);

    f.render_widget(
        Paragraph::new(" 🌿 Holly TUI — Register ")
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::NONE)),
        chunks[0],
    );

    let email_block = if app.auth.focused == LoginField::Email { focused_block(" Email ") }
                      else { titled_block(" Email ") };
    f.render_widget(Paragraph::new(app.auth.register_email.as_str()).block(email_block), chunks[1]);

    let pw_block = if app.auth.focused == LoginField::Password { focused_block(" Password ") }
                   else { titled_block(" Password ") };
    f.render_widget(
        Paragraph::new("*".repeat(app.auth.register_password.len())).block(pw_block),
        chunks[2],
    );

    f.render_widget(
        Paragraph::new("Enter: register  Tab: switch field  Esc: back to login")
            .style(Style::default().fg(Color::DarkGray)).alignment(Alignment::Center),
        chunks[3],
    );
    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), chunks[5]);
}

pub fn render_forgot_password(f: &mut Frame, app: &App) {
    let popup = centered_rect(60, 40, f.area());
    let chunks = Layout::vertical([
        Constraint::Length(3), Constraint::Length(3), Constraint::Length(3),
        Constraint::Min(0),    Constraint::Length(2),
    ]).split(popup);

    f.render_widget(
        Paragraph::new(" 🌿 Holly TUI — Forgot Password ")
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
            .alignment(Alignment::Center)
            .block(Block::default().borders(Borders::NONE)),
        chunks[0],
    );
    f.render_widget(
        Paragraph::new(app.auth.forgot_email.as_str()).block(focused_block(" Email ")),
        chunks[1],
    );
    f.render_widget(
        Paragraph::new("Enter: send reset email  Esc: back to login")
            .style(Style::default().fg(Color::DarkGray)).alignment(Alignment::Center),
        chunks[2],
    );
    f.render_widget(status_bar(app.status_msg.as_deref(), app.error_msg.as_deref()), chunks[4]);
}
