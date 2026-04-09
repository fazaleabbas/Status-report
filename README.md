# Status Report Presentation

A professional status report generator with local AI analysis (Ollama + llama3.2).
Creates PowerPoint decks with visual RAG indicators, polished executive content,
and smart project analysis — all on your Mac without internet or API keys.

## Installation

The easiest way to get started is to run the automated installer:

```bash
cd /path/to/Status\ report
chmod +x install.sh
./install.sh
```

The installer will:
1. Install Ollama (if needed) via Homebrew
2. Download the llama3.2 AI model
3. Configure Ollama to run in the background
4. Install Python dependencies
5. Build the macOS app
6. (Optional) Copy app to Applications folder

After installation, launch the app:
- From Applications folder
- Or: `open /Applications/status-report-form.app`
- Or: Search "status report" in Spotlight (Cmd+Space)

See `INSTALLATION.md` for post-install details.

## Files

- `project_statuses.json` — source data for the project updates
- `generate_status_report.py` — creates the `.pptx` presentation
- `status_report_form.py` — simple desktop form to enter project name and status
- `analyse_projects.py` — local LLM analysis pipeline with fallback
- `validate_presentation.py` — checks that the generated deck exists and contains the expected content
- `requirements.txt` — Python dependency list
- `install.sh` — automated setup and build
- `INSTALLATION.md` — post-install guide

## Quick start (form UI) — Alternative manual run

If you didn't use the installer or want to run from source:

```bash
cd "/Users/fazaleabbas/Projects/Status report"
python3 -m pip install -r requirements.txt
python3 status_report_form.py
```

This assumes Ollama is already running separately:
```bash
ollama serve
```

In the form:

1. Enter `Project name` and `Project status`
2. Optionally choose `RAG` (`Auto`, `Green`, `Amber`, `Red`)
3. Click `Add project`
4. Repeat for all projects
5. Click `Generate PowerPoint` and choose where to save

## Quick start (file-based)

```bash
cd "/Users/fazaleabbas/Projects/Status report"
python3 generate_status_report.py --input project_statuses.json --output status-report-2026-04-09.pptx
python3 validate_presentation.py status-report-2026-04-09.pptx
```

## Simple input JSON (name + status only)

Use this mode if you want to keep source data in a smaller JSON file:

```json
[
  {"name": "Project A", "status": "Development completed and moving to testing.", "rag": "green"},
  {"name": "Project B", "status": "Pending vendor response, currently at risk."}
]
```

`rag` is optional. If omitted, the generator infers RAG from the status text.
Accepted values for `rag`: `green`, `amber`, `red`, or `auto`.

Generate from this format:

```bash
python3 generate_status_report.py --simple-input simple_projects.json --title "Weekly Status" --report-date "09 April 2026" --output status-report-simple.pptx
python3 validate_presentation.py status-report-simple.pptx --require-text "Project A"
```

## Customize the status data

Edit `project_statuses.json` and update:

- `report_title`
- `report_date`
- `portfolio_summary`
- `projects[]` entries, including `name`, `rag`, `progress`, `status`, `next_step`, and `notes`

Supported RAG values:

- `green`
- `amber`
- `red`

## Output

The generated presentation is saved to the path you provide with `--output`.

## AI analysis with local LLM (Ollama)

The program can analyse and enrich raw project inputs with a local LLM before
generating the deck. This produces polished executive-ready status text,
accurate RAG inference, meaningful progress labels, next steps, and notes —
instead of generic placeholders.

### Recommended model: `llama3.2`

Install once:

```bash
brew install ollama
ollama pull llama3.2
ollama serve          # keep running in background
```

### Form UI (AI mode)

1. Tick **Analyse projects with local LLM before generating**
2. Confirm the model name (default: `llama3.2`)
3. Click **Check Ollama status** to verify
4. Click **Generate PowerPoint** — analysis runs per project before the deck is built

### CLI with analysis

```bash
python3 generate_status_report.py \
  --simple-input simple_projects.json \
  --analyse \
  --model llama3.2 \
  --output status-report-ai.pptx
```

### Fallback behaviour

If Ollama is not running or the model is missing, the generator silently falls
back to rule-based enrichment so the program never crashes.

### How the analysis works

For each project the LLM receives:
- project name
- raw status text

And returns structured JSON containing:
- `rag` — green / amber / red
- `progress` — short phrase (e.g. "80% Complete", "Discovery Stage")
- `status` — one polished executive sentence
- `next_step` — one clear action
- `notes` — two key consideration bullets

A second LLM call produces the portfolio-level executive summary paragraph.

## Build a native macOS app bundle

Because this workspace is on macOS, the native packaged output is a macOS `.app` bundle, not a Windows `.exe` file.

Build it with:

```bash
cd "/Users/fazaleabbas/Projects/Status report"
chmod +x build_macos_executable.sh
./build_macos_executable.sh
```

This creates:

- `dist/status-report-form.app`
- `status-report-form-macos-app.zip`

Run the packaged app with:

```bash
cd "/Users/fazaleabbas/Projects/Status report"
open "dist/status-report-form.app"
```

If you still want the raw packaged binary inside the app bundle, it will be available under the `.app` package contents generated by PyInstaller.

