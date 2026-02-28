//! Keyboard event handlers and async data loaders.

use crossterm::event::{KeyCode, KeyModifiers};
use tokio::sync::mpsc;
use anyhow::Result;

use crate::app::state::*;
use crate::events::{AppEvent, is_quit};

impl App {
    pub async fn handle_event(&mut self, event: AppEvent) -> Result<()> {
        match event {
            AppEvent::Tick => self.on_tick().await?,
            AppEvent::Key(key) => {
                if is_quit(&key) { self.quit = true; return Ok(()); }
                if key.code == KeyCode::Esc { self.handle_escape(); return Ok(()); }
                match &self.current_screen.clone() {
                    Screen::Login            => self.handle_login_key(key).await?,
                    Screen::Register         => self.handle_register_key(key).await?,
                    Screen::ForgotPassword   => self.handle_forgot_key(key).await?,
                    Screen::Dashboard        => self.handle_dashboard_key(key).await?,
                    Screen::Missions         => self.handle_missions_key(key).await?,
                    Screen::MissionDetail(id) => { let id = id.clone(); self.handle_mission_detail_key(key, &id).await?; }
                    Screen::Chat(conv_id)    => { let id = conv_id.clone(); self.handle_chat_key(key, &id).await?; }
                    Screen::Github           => self.handle_github_key(key).await?,
                    Screen::Llms             => self.handle_llms_key(key).await?,
                    Screen::Settings         => self.handle_settings_key(key).await?,
                    Screen::Notifications    => self.handle_notifications_key(key).await?,
                    Screen::Wizard           => self.handle_wizard_key(key).await?,
                    Screen::Loading(..)      => {}
                }
            }
            AppEvent::Resize(..) => {}
        }
        Ok(())
    }

    fn handle_escape(&mut self) {
        match &self.current_screen.clone() {
            Screen::Register | Screen::ForgotPassword => self.navigate_to(Screen::Login),
            Screen::Dashboard => {}
            Screen::Missions | Screen::Chat(_) | Screen::Github | Screen::Llms
            | Screen::Settings | Screen::Notifications | Screen::Wizard => {
                self.navigate_to(Screen::Dashboard);
            }
            Screen::MissionDetail(_) => self.navigate_to(Screen::Missions),
            _ => {}
        }
    }

    // --- Tick: drain the SSE token channel for non-blocking streaming ---

    async fn on_tick(&mut self) -> Result<()> {
        self.drain_streaming_tokens();
        Ok(())
    }

    /// Pull all pending tokens from the channel and append to the streaming buffer.
    /// Called every 200ms tick so the TUI re-renders incrementally without blocking.
    fn drain_streaming_tokens(&mut self) {
        if self.chat.phase != ChatPhase::Streaming { return; }
        let Some(rx) = &mut self.chat.token_rx else { return };
        loop {
            match rx.try_recv() {
                Ok(token) if token == "\x00DONE\x00" => {
                    // Streaming complete — commit the buffered response
                    let content = std::mem::take(&mut self.chat.streaming_buffer);
                    self.chat.messages.push(("assistant".into(), content));
                    self.chat.phase = ChatPhase::Idle;
                    self.chat.token_rx = None;
                    break;
                }
                Ok(token) => self.chat.streaming_buffer.push_str(&token),
                Err(mpsc::error::TryRecvError::Empty) => break,
                Err(mpsc::error::TryRecvError::Disconnected) => {
                    // Task exited without sending DONE — still commit what we have
                    if !self.chat.streaming_buffer.is_empty() {
                        let content = std::mem::take(&mut self.chat.streaming_buffer);
                        self.chat.messages.push(("assistant".into(), content));
                    }
                    self.chat.phase = ChatPhase::Idle;
                    self.chat.token_rx = None;
                    break;
                }
            }
        }
    }

    // ---------- Login ----------

    async fn handle_login_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Tab => {
                self.auth.focused = match self.auth.focused {
                    LoginField::Email    => LoginField::Password,
                    LoginField::Password => LoginField::Email,
                };
            }
            KeyCode::Enter => {
                if self.auth.email.is_empty() || self.auth.password.is_empty() {
                    self.set_error("Email and password are required");
                    return Ok(());
                }
                self.set_status("Logging in…");
                let email = self.auth.email.clone();
                let password = self.auth.password.clone();
                match self.client.auth().login(&email, &password).await {
                    Ok(_) => {
                        self.set_status("Logged in!");
                        self.load_dashboard().await?;
                        self.navigate_to(Screen::Dashboard);
                    }
                    Err(e) => self.set_error(format!("Login failed: {e}")),
                }
            }
            KeyCode::Char('r') if key.modifiers == KeyModifiers::CONTROL => {
                self.navigate_to(Screen::Register);
            }
            KeyCode::Char('f') if key.modifiers == KeyModifiers::CONTROL => {
                self.navigate_to(Screen::ForgotPassword);
            }
            KeyCode::Char(c) => match self.auth.focused {
                LoginField::Email    => self.auth.email.push(c),
                LoginField::Password => self.auth.password.push(c),
            },
            KeyCode::Backspace => match self.auth.focused {
                LoginField::Email    => { self.auth.email.pop(); }
                LoginField::Password => { self.auth.password.pop(); }
            },
            _ => {}
        }
        Ok(())
    }

    // ---------- Register ----------

    async fn handle_register_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.auth.register_email.is_empty() || self.auth.register_password.is_empty() {
                    self.set_error("Email and password required");
                    return Ok(());
                }
                let email = self.auth.register_email.clone();
                let password = self.auth.register_password.clone();
                match self.client.auth().register(&email, &password).await {
                    Ok(_) => {
                        self.set_status("Registered! Please log in.");
                        self.auth.email = email;
                        self.navigate_to(Screen::Login);
                    }
                    Err(e) => self.set_error(format!("Register failed: {e}")),
                }
            }
            KeyCode::Tab => {
                self.auth.focused = match self.auth.focused {
                    LoginField::Email    => LoginField::Password,
                    LoginField::Password => LoginField::Email,
                };
            }
            KeyCode::Char(c) => match self.auth.focused {
                LoginField::Email    => self.auth.register_email.push(c),
                LoginField::Password => self.auth.register_password.push(c),
            },
            KeyCode::Backspace => match self.auth.focused {
                LoginField::Email    => { self.auth.register_email.pop(); }
                LoginField::Password => { self.auth.register_password.pop(); }
            },
            _ => {}
        }
        Ok(())
    }

    // ---------- Forgot password ----------

    async fn handle_forgot_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.auth.forgot_email.is_empty() {
                    self.set_error("Email required");
                    return Ok(());
                }
                let email = self.auth.forgot_email.clone();
                match self.client.auth().request_password_reset(&email).await {
                    Ok(_) => {
                        self.set_status("Reset email sent (if account exists)");
                        self.navigate_to(Screen::Login);
                    }
                    Err(e) => self.set_error(format!("Error: {e}")),
                }
            }
            KeyCode::Char(c)  => self.auth.forgot_email.push(c),
            KeyCode::Backspace => { self.auth.forgot_email.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Dashboard ----------

    async fn handle_dashboard_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('1') | KeyCode::Char('c') => {
                if self.chat.conversations.is_empty() { self.load_conversations().await?; }
                let conv_id = self.chat.conversations.first().map(|c| c.id.clone()).unwrap_or_default();
                self.navigate_to(Screen::Chat(conv_id));
            }
            KeyCode::Char('2') | KeyCode::Char('g') => {
                self.load_repos().await?;
                self.navigate_to(Screen::Github);
            }
            KeyCode::Char('3') | KeyCode::Char('m') => {
                self.load_missions().await?;
                self.navigate_to(Screen::Missions);
            }
            KeyCode::Char('4') | KeyCode::Char('l') => {
                self.load_llms().await?;
                self.navigate_to(Screen::Llms);
            }
            KeyCode::Char('5') | KeyCode::Char('s') => self.navigate_to(Screen::Settings),
            KeyCode::Char('n') => {
                self.load_notifications().await?;
                self.navigate_to(Screen::Notifications);
            }
            KeyCode::Char('w') => self.navigate_to(Screen::Wizard),
            _ => {}
        }
        Ok(())
    }

    // ---------- Missions ----------

    async fn handle_missions_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        // If a create modal is open, route input there
        if self.missions.action == MissionAction::Creating {
            return self.handle_create_mission_input(key).await;
        }
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.missions.list.len();
                let mut idx = self.missions.selected_idx;
                self.list_up(len, &mut idx);
                self.missions.selected_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.missions.list.len();
                let mut idx = self.missions.selected_idx;
                self.list_down(len, &mut idx);
                self.missions.selected_idx = idx;
            }
            KeyCode::Enter => {
                if let Some(m) = self.missions.list.get(self.missions.selected_idx) {
                    let id = m.id.clone();
                    match self.client.missions().get(&id).await {
                        Ok(detail) => {
                            self.missions.current = Some(detail);
                            self.navigate_to(Screen::MissionDetail(id));
                        }
                        Err(e) => self.set_error(format!("Failed to load mission: {e}")),
                    }
                }
            }
            KeyCode::Char('n') => {
                self.missions.action = MissionAction::Creating;
                self.missions.new_name.clear();
            }
            KeyCode::Char('r') => {
                self.load_missions().await?;
                self.set_status("Refreshed");
            }
            _ => {}
        }
        Ok(())
    }

    async fn handle_create_mission_input(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.missions.new_name.is_empty() {
                    self.set_error("Mission name required");
                    return Ok(());
                }
                let name = self.missions.new_name.clone();
                match self.client.missions().create(holly_client::models::MissionCreate {
                    name,
                    description: None,
                    llm_id: None,
                }).await {
                    Ok(m) => {
                        self.set_status(format!("Created mission '{}'", m.name));
                        self.missions.action = MissionAction::None;
                        self.load_missions().await?;
                    }
                    Err(e) => self.set_error(format!("Failed to create: {e}")),
                }
            }
            KeyCode::Esc => {
                self.missions.action = MissionAction::None;
                self.missions.new_name.clear();
            }
            KeyCode::Char(c)  => self.missions.new_name.push(c),
            KeyCode::Backspace => { self.missions.new_name.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Mission Detail ----------

    async fn handle_mission_detail_key(&mut self, key: crossterm::event::KeyEvent, id: &str) -> Result<()> {
        let id = id.to_string();
        match key.code {
            KeyCode::Char('s') => {
                self.set_status("Starting mission…");
                match self.client.missions().start(&id).await {
                    Ok(_) => self.set_status("Mission started!"),
                    Err(e) => self.set_error(format!("Start failed: {e}")),
                }
            }
            KeyCode::Char('e') => {
                match self.client.missions().end(&id, holly_client::models::MissionStateUpdate {
                    state: holly_client::models::MissionState::Completed,
                }).await {
                    Ok(_) => { self.set_status("Mission ended"); self.navigate_to(Screen::Missions); }
                    Err(e) => self.set_error(format!("End failed: {e}")),
                }
            }
            KeyCode::Char('c') => {
                match self.client.missions().create_conversation(&id, holly_client::models::MissionConversationCreate {
                    title: None,
                    llm_id: None,
                }).await {
                    Ok(resp) => {
                        let conv_id = resp.conversation_id.unwrap_or_default();
                        self.navigate_to(Screen::Chat(conv_id));
                    }
                    Err(e) => self.set_error(format!("Create conversation failed: {e}")),
                }
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Chat (non-blocking SSE) ----------

    async fn handle_chat_key(&mut self, key: crossterm::event::KeyEvent, conv_id: &str) -> Result<()> {
        // Ignore input while streaming — don't block
        if self.chat.phase == ChatPhase::Streaming { return Ok(()); }
        let conv_id = conv_id.to_string();
        match key.code {
            KeyCode::Enter => {
                let msg = self.chat.input.trim().to_string();
                if msg.is_empty() { return Ok(()); }
                self.chat.input.clear();
                self.chat.messages.push(("user".into(), msg.clone()));
                self.chat.phase = ChatPhase::Streaming;
                self.chat.streaming_buffer.clear();

                // Spawn SSE task — tokens arrive via the channel, drained on each Tick
                let (tx, rx) = mpsc::unbounded_channel::<String>();
                self.chat.token_rx = Some(rx);

                let client = self.client.clone();
                tokio::spawn(async move {
                    let _ = client.conversations().send_message_sse(
                        &conv_id,
                        &msg,
                        |token| { let _ = tx.send(token); },
                    ).await;
                    let _ = tx.send("\x00DONE\x00".into());
                });
            }
            KeyCode::Char(c)  => self.chat.input.push(c),
            KeyCode::Backspace => { self.chat.input.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- GitHub ----------

    async fn handle_github_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.github.repositories.len();
                let mut idx = self.github.selected_idx;
                self.list_up(len, &mut idx);
                self.github.selected_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.github.repositories.len();
                let mut idx = self.github.selected_idx;
                self.list_down(len, &mut idx);
                self.github.selected_idx = idx;
            }
            KeyCode::Char('r') => { self.load_repos().await?; self.set_status("Refreshed"); }
            _ => {}
        }
        Ok(())
    }

    // ---------- LLMs ----------

    async fn handle_llms_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.llm.llms.len();
                let mut idx = self.llm.selected_idx;
                self.list_up(len, &mut idx);
                self.llm.selected_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.llm.llms.len();
                let mut idx = self.llm.selected_idx;
                self.list_down(len, &mut idx);
                self.llm.selected_idx = idx;
            }
            KeyCode::Char('r') => { self.load_llms().await?; self.set_status("Refreshed"); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Settings ----------

    async fn handle_settings_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Tab => {
                self.settings.tab = match self.settings.tab {
                    SettingsTab::General => SettingsTab::Llm,
                    SettingsTab::Llm     => SettingsTab::Github,
                    SettingsTab::Github  => SettingsTab::About,
                    SettingsTab::About   => SettingsTab::General,
                };
            }
            KeyCode::Enter if self.settings.tab == SettingsTab::General => {
                self.config.server_url = self.settings.server_url.clone();
                if let Err(e) = self.config.save() {
                    self.set_error(format!("Save failed: {e}"));
                } else {
                    self.set_status("Settings saved");
                }
            }
            KeyCode::Char(c)  if self.settings.tab == SettingsTab::General => {
                self.settings.server_url.push(c);
            }
            KeyCode::Backspace if self.settings.tab == SettingsTab::General => {
                self.settings.server_url.pop();
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Notifications ----------

    async fn handle_notifications_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('a') => {
                match self.client.notifications().mark_all_read().await {
                    Ok(_) => { self.set_status("All marked as read"); self.load_notifications().await?; }
                    Err(e) => self.set_error(format!("Error: {e}")),
                }
            }
            KeyCode::Char('r') => { self.load_notifications().await?; self.set_status("Refreshed"); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Wizard ----------

    async fn handle_wizard_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('1') => { self.load_repos().await?;    self.navigate_to(Screen::Github); }
            KeyCode::Char('2') => { self.load_missions().await?; self.navigate_to(Screen::Missions); }
            KeyCode::Char('3') => self.navigate_to(Screen::Settings),
            _ => {}
        }
        Ok(())
    }

    // ---------- Data loaders ----------

    pub async fn load_dashboard(&mut self) -> Result<()> {
        let missions_svc = self.client.missions();
        let github_svc   = self.client.github();
        let (m, r) = tokio::join!(missions_svc.list(), github_svc.list_repositories());
        self.dashboard.missions_count = m.map(|v| v.len()).unwrap_or(0);
        self.dashboard.repos_count    = r.map(|v| v.len()).unwrap_or(0);
        Ok(())
    }

    pub async fn load_missions(&mut self) -> Result<()> {
        match self.client.missions().list().await {
            Ok(m)  => self.missions.list = m,
            Err(e) => self.set_error(format!("Load missions failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_conversations(&mut self) -> Result<()> {
        match self.client.conversations().list().await {
            Ok(c) => {
                self.dashboard.conversations_count = c.len();
                self.dashboard.recent_conversations = c.iter().take(5).cloned().collect();
                self.chat.conversations = c;
            }
            Err(e) => self.set_error(format!("Load conversations failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_repos(&mut self) -> Result<()> {
        match self.client.github().list_repositories().await {
            Ok(r)  => self.github.repositories = r,
            Err(e) => self.set_error(format!("Load repos failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_llms(&mut self) -> Result<()> {
        // Single service handle; list_with_keys() runs both requests concurrently internally
        match self.client.llms().list_with_keys().await {
            Ok((llms, keys)) => { self.llm.llms = llms; self.llm.api_keys = keys; }
            Err(e) => self.set_error(format!("Load LLMs failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_notifications(&mut self) -> Result<()> {
        match self.client.notifications().list_with_unread().await {
            Ok((list, count)) => {
                self.notifications.notifications = list.results;
                self.notifications.unread_count = count.count;
            }
            Err(e) => self.set_error(format!("Load notifications failed: {e}")),
        }
        Ok(())
    }
}
