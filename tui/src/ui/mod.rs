//! UI rendering — one function per screen, composed from Ratatui widgets.

mod login;
mod dashboard;
mod missions;
mod chat;
mod github;
mod llms;
mod settings;
mod notifications;
mod wizard;
mod helpers;

pub use helpers::{centered_rect, status_bar, render_tabs};

use ratatui::prelude::*;
use crate::app::state::{App, Screen};

/// Top-level render dispatch.
pub fn draw(f: &mut Frame, app: &App) {
    match &app.current_screen {
        Screen::Login => login::render_login(f, app),
        Screen::Register => login::render_register(f, app),
        Screen::ForgotPassword => login::render_forgot_password(f, app),
        Screen::Dashboard => dashboard::render_dashboard(f, app),
        Screen::Missions => missions::render_missions(f, app),
        Screen::MissionDetail(id) => missions::render_mission_detail(f, app, id),
        Screen::Chat(conv_id) => chat::render_chat(f, app, conv_id),
        Screen::Github => github::render_github(f, app),
        Screen::Llms => llms::render_llms(f, app),
        Screen::Settings => settings::render_settings(f, app),
        Screen::Notifications => notifications::render_notifications(f, app),
        Screen::Wizard => wizard::render_wizard(f, app),
        Screen::Loading(msg, _) => render_loading(f, msg),
    }
}

fn render_loading(f: &mut Frame, msg: &str) {
    use ratatui::widgets::{Block, Borders, Paragraph};
    use ratatui::layout::Alignment;
    let area = centered_rect(50, 20, f.area());
    let p = Paragraph::new(format!("⏳ {msg}"))
        .block(Block::default().borders(Borders::ALL).title(" Loading "))
        .alignment(Alignment::Center);
    f.render_widget(p, area);
}
