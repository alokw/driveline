# Screenshots Guide

This directory contains screenshots for the README.md file.

## Required Screenshots

### 1. Main Dashboard (`01-main-dashboard.png`)
- **What to capture**: The main dashboard page showing:
  - Show close countdown display
  - Sequence time FYI
  - Next showtime display
  - D3 cue buttons (standard and clean)
  - StageTimer controls
  - Showtime schedule buttons
- **Tips**: Make sure the page is fully loaded and showing live data
- **Size**: 1200-1400px wide recommended

### 2. Status Page (`02-status-page.png`)
- **What to capture**: The status page showing:
  - System status indicators
  - OSC connection status
  - Live automation values (wall positions, turntable rotation)
  - D3 status information
- **Tips**: Show the page with live data updating
- **Size**: 1200-1400px wide recommended

### 3. Advanced Controls (`03-advanced-controls.png`)
- **What to capture**: The advanced controls page showing:
  - EventMaster preset buttons (primary, secondary, etc.)
  - Millumin column launch buttons
  - Advanced d3 cue controls
  - Any custom timer presets
- **Tips**: Show all available controls
- **Size**: 1200-1400px wide recommended

### 4. Debug Page (`04-debug-page.png`)
- **What to capture**: The debug page showing:
  - Real-time OSC database table
  - All monitored OSC paths and current values
  - Auto-refreshing data
- **Tips**: Capture with live data showing multiple OSC paths
- **Size**: Full page width recommended to show table

### 5. Component System (`05-component-system.png`)
- **What to capture**: Either:
  - A side-by-side comparison of verbose HTML vs macro usage
  - Code editor showing the macro components in `templates/components.html`
  - A rendered dashboard with annotations pointing out macro usage
- **Tips**: This demonstrates the code simplification benefit
- **Size**: 1200-1400px wide recommended

## How to Add Screenshots

1. Take screenshots using your preferred tool:
   - **macOS**: Cmd+Shift+4 (system), or use Skitch/Preview
   - **Windows**: Win+Shift+S (Snipping Tool)
   - **Linux**: gnome-screenshot, Shutter, or Spectacle

2. Save files to this directory with the exact names specified above

3. Recommended formats:
   - **PNG**: For screenshots with text, UI elements, or diagrams (lossless)
   - **JPEG**: For photographic images or complex graphics (smaller file size)

4. Optimize file sizes:
   - PNG: Use TinyPNG (https://tinypng.com) or `optipng` command
   - Keep files under 500KB each if possible
   - GitHub will serve them at their original size

5. Commit screenshots:
   ```bash
   git add screenshots/
   git commit -m "Add screenshots to README"
   ```

## File Naming Convention

Use the format: `NN-description.png`

- `NN`: Two-digit number (01-99) for ordering
- `description`: Short kebab-case description

Example: `01-main-dashboard.png`

## GitHub README Image Syntax

Images are referenced in README.md using standard Markdown:

```markdown
![Alt text](./screenshots/01-main-dashboard.png)
```

The `./screenshots/` path ensures images load correctly whether viewing:
- The README on GitHub
- A local clone of the repo
- Rendered documentation (if you add it later)
