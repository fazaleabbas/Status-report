# Status Report Generator — Installation Complete

Thank you for installing the **Status Report Generator**!

## What was installed

- **Ollama** — local LLM server (no internet required, no API key)
- **llama3.2** — AI model for project analysis
- **Python dependencies** — PowerPoint generation libraries
- **macOS app bundle** — ready to launch

## First launch

Ollama will start automatically the next time you restart your Mac.

To start it now:

```bash
brew services start ollama
```

Then launch the app:

```bash
open /Applications/status-report-form.app
```

Or search for **"status report"** in Spotlight (Cmd+Space).

## How to use

1. **Enter project details** in the form:
   - Project name
   - Status description
   - RAG (optional: Auto / Green / Amber / Red)

2. **Enable AI analysis** (optional):
   - Tick "Analyse projects with local LLM"
   - Click "Check Ollama status" to confirm it's running
   - AI will enrich your status text into executive-ready content

3. **Generate the presentation**:
   - Click "Generate PowerPoint"
   - Choose where to save
   - Done!

## Manage Ollama

View logs:
```bash
tail -f /tmp/ollama.log
```

Stop Ollama (if needed):
```bash
brew services stop ollama
```

Restart Ollama:
```bash
brew services restart ollama
```

## Troubleshooting

### "Ollama is not reachable"
```bash
brew services start ollama
sleep 3
# Try again in the app
```

### "Model not found"
Re-run the installer or pull manually:
```bash
ollama pull llama3.2
```

### App won't open
Try from terminal:
```bash
/Applications/status-report-form.app/Contents/MacOS/status-report-form
```

## More info

- **Project repo:** https://github.com/fazaleabbas/Status-report
- **Ollama docs:** https://ollama.ai
- **Report features:** RAG indicators, executive summaries, analysis

---

Enjoy! 🎉

