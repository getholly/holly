use ratatui::prelude::*;
use ratatui::widgets::{Block, Borders, Paragraph, Tabs};
use ratatui::style::{Color, Modifier, Style};

pub fn centered_rect(percent_x: u16, percent_y: u16, area: Rect) -> Rect {
    let vert = Layout::vertical([
        Constraint::Percentage((100 - percent_y) / 2),
        Constraint::Percentage(percent_y),
        Constraint::Percentage((100 - percent_y) / 2),
    ]).split(area);
    Layout::horizontal([
        Constraint::Percentage((100 - percent_x) / 2),
        Constraint::Percentage(percent_x),
        Constraint::Percentage((100 - percent_x) / 2),
    ]).split(vert[1])[1]
}

pub fn status_bar<'a>(status: Option<&'a str>, error: Option<&'a str>) -> Paragraph<'a> {
    let (text, style) = if let Some(err) = error {
        (err, Style::default().fg(Color::Red).add_modifier(Modifier::BOLD))
    } else if let Some(ok) = status {
        (ok, Style::default().fg(Color::Green))
    } else {
        ("", Style::default().fg(Color::DarkGray))
    };
    Paragraph::new(text)
        .block(Block::default().borders(Borders::TOP))
        .style(style)
}

/// `titles` is a plain slice — no allocation at the call site.
pub fn render_tabs<'a>(titles: &[&'a str], selected: usize) -> Tabs<'a> {
    Tabs::new(titles.to_vec())
        .select(selected)
        .style(Style::default().fg(Color::DarkGray))
        .highlight_style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .divider("|")
}

/// Standard page layout: [content area, status bar (2 lines)]
pub fn page_layout(area: Rect) -> (Rect, Rect) {
    let chunks = Layout::vertical([Constraint::Min(0), Constraint::Length(2)]).split(area);
    (chunks[0], chunks[1])
}

pub fn selected_style() -> Style {
    Style::default().fg(Color::Black).bg(Color::Cyan).add_modifier(Modifier::BOLD)
}
pub fn normal_style()   -> Style { Style::default().fg(Color::White) }
pub fn muted_style()    -> Style { Style::default().fg(Color::DarkGray) }

pub fn titled_block(title: &str) -> Block {
    Block::default().title(title).borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Blue))
}
pub fn focused_block(title: &str) -> Block {
    Block::default().title(title).borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Cyan))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn centered_rect_is_within_parent() {
        let area = Rect::new(0, 0, 100, 50);
        let c = centered_rect(60, 40, area);
        assert!(c.x >= area.x && c.right() <= area.right());
        assert!(c.y >= area.y && c.bottom() <= area.bottom());
    }

    #[test]
    fn centered_rect_smaller_than_parent() {
        let area = Rect::new(0, 0, 100, 50);
        let c = centered_rect(50, 50, area);
        assert!(c.width < area.width && c.height < area.height);
    }

    #[test]
    fn page_layout_splits_correctly() {
        let area = Rect::new(0, 0, 100, 50);
        let (content, status) = page_layout(area);
        assert_eq!(status.height, 2);
        assert_eq!(content.height + status.height, area.height);
    }

    #[test]
    fn render_tabs_accepts_slice() {
        // Compile-time check — slice literal, no Vec allocation
        let _ = render_tabs(&["General", "LLM", "GitHub"], 0);
    }
}
