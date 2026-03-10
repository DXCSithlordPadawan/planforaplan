# AI Application Generator — User Guide

**Version:** 2.1
**Date:** 2026-03-10
**Audience:** End users, technical presenters, product managers

---

## Table of Contents

1. [What This Application Does](#1-what-this-application-does)
2. [Before You Begin](#2-before-you-begin)
3. [Starting the Application](#3-starting-the-application)
4. [Step-by-Step Workflow](#4-step-by-step-workflow)
5. [Writing Effective Requirements](#5-writing-effective-requirements)
6. [Understanding the Plan View](#6-understanding-the-plan-view)
7. [Understanding the Execution View](#7-understanding-the-execution-view)
8. [Understanding the Success View](#8-understanding-the-success-view)
9. [Stopping a Running Application](#9-stopping-a-running-application)
10. [Starting a New Generation](#10-starting-a-new-generation)
11. [Common Errors and Fixes](#11-common-errors-and-fixes)
12. [Tips for Demonstrations](#12-tips-for-demonstrations)
13. [Frequently Asked Questions](#13-frequently-asked-questions)

---

## 1. What This Application Does

The AI Application Generator takes a plain English description of a web application and — within a few minutes — produces a fully functional, locally-running Python web app that opens automatically in your browser.

The process works in two stages:

**Stage 1 — Plan:** You describe what you want. The AI generates a detailed implementation plan. You read it, edit it if needed, and approve it.

**Stage 2 — Generate and Deploy:** The AI writes all the code. The system copies it to a deployment folder, installs any extra dependencies, starts a local web server, and opens your browser at the running application.

You do not need to write any code, open a terminal, or install any additional tools once setup is complete.

---

## 2. Before You Begin

### Requirements

- **Python 3.11 or later** installed on your machine ([python.org](https://python.org))
- **An API key** for one of the supported AI providers
- **Internet access** for AI API calls and for loading the Tailwind CSS stylesheet in generated apps
- The application has been set up (i.e. `setup.bat` or `setup.ps1` has been run successfully)

### Supported AI Providers

**Claude (Anthropic):**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Navigate to API Keys and create a new key (starts with `sk-ant-`)

**Gemini (Google):**
1. Visit [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API key** and create a new key (starts with `AIzaSy`)
3. Note: The free tier allows 15 requests/minute and 1,500 requests/day

**Minimax:**
1. Visit [platform.minimax.io](https://platform.minimax.io)
2. Navigate to API Keys and create a new key (JWT format, starts with `eyJ`)

**Custom (OpenAI-compatible):**
Any provider that exposes the OpenAI chat completions API format can be used — including OpenAI itself, OpenRouter, Ollama (local), LM Studio, Azure OpenAI, Mistral, and others. You will need:
- The **Base URL** of the API endpoint (e.g. `https://api.openai.com/v1`, `http://localhost:11434/v1`)
- The **Model name** expected by that service (e.g. `gpt-4o`, `llama3`)
- Your **API key** for the service

Keep your API key private. Do not share it or paste it anywhere other than the configuration panel in this application.

---

## 3. Starting the Application

Open a Command Prompt or PowerShell window, navigate to the application folder, and run:

```
start.bat
```
or
```
.\start.ps1
```

You will see a message like:

```
Starting AI Application Generator on http://127.0.0.1:8000
Press Ctrl+C to stop.
```

Open your web browser and go to:

```
http://127.0.0.1:8000
```

The AI Application Generator interface will load. Leave the terminal window open — the server runs there.

To stop the orchestrator, press **Ctrl+C** in the terminal window.

---

## 4. Step-by-Step Workflow

### Step 1 — Configure the AI Provider

In the **AI Provider Configuration** panel:

1. Select your provider from the dropdown: **Claude (Anthropic)**, **Gemini (Google)**, **Minimax**, or **Custom (OpenAI-compatible)**.
2. Paste your API key into the **API Key** field.
3. If you selected **Custom (OpenAI-compatible)**, two additional fields appear:
   - **Base URL** — the root URL of the API, e.g. `https://openrouter.ai/api/v1`
   - **Model** — the model identifier, e.g. `anthropic/claude-3.5-sonnet`
4. Click **Validate & Save**.

You only need to do this once per session. The key is held in memory and will be cleared when you close the server.

### Step 2 — Describe Your Application

Click into the large text area and type a description of the web application you want to build.

Example: `Build a to-do list application where users can add tasks, mark them as complete, and delete them. Show incomplete tasks highlighted in yellow.`

### Step 3 — Generate the Plan

Click **Generate Plan**. This typically takes 15–60 seconds depending on your provider.

### Step 4 — Review and Approve the Plan

The Plan view shows your original requirement on the left (read-only) and the AI-generated implementation plan on the right (editable).

Edit the plan if needed. Click **↻ Regenerate Plan** for a completely fresh plan. When satisfied, click **Submit for Execution →**.

### Step 5 — Wait for Deployment

The Execution view shows a progress bar and scrolling terminal log. Watch each step:

1. AI generating application code (may take 1–5 minutes for complex apps)
2. Parsing generated files
3. Copying base template
4. Writing generated files
5. Installing any extra dependencies
6. Starting the application server
7. Launching your browser

### Step 6 — Use Your Application

When deployment is complete, your browser opens automatically at `http://127.0.0.1:8001` showing the generated application.

---

## 5. Writing Effective Requirements

### Be Specific About Features

| Vague | Better |
|-------|--------|
| "Make a shopping app" | "Build a product catalogue with a list of items, each showing name, price, and a short description. Include a search bar to filter by name." |
| "A dashboard" | "Create a data dashboard showing four summary cards: total sales, average order value, number of customers, and top product. Use placeholder data." |

### State the Visual Style if It Matters

Include style direction: "Use a clean minimalist design with a white background and blue accent colour" or "Dark theme with a sidebar navigation."

### Mention Data Requirements

"Use hardcoded sample data for five products" or "Use a JSON file to store tasks."

### Exclude What You Do Not Need

"Do not include user authentication" or "No database required — just in-memory storage for this demo."

### Aim for 50–200 Words

Short requirements produce minimal applications. Detailed requirements (100–200 words) produce richer results.

---

## 6. Understanding the Plan View

The plan is a markdown document structured with headings for:

- **File Structure** — every file the AI intends to create
- **Component Breakdown** — what each file does
- **Technical Approach** — libraries, data flow, URL structure
- **Implementation Steps** — the build order

Edit freely — the plan is passed directly to Stage 2 as instructions. If the plan looks completely wrong, click **Regenerate Plan**.

---

## 7. Understanding the Execution View

**Phase label and percentage** — Current step and overall progress (0–100%).

**Terminal log panel** — Scrolling dark panel with real-time messages:
- **White/grey** — informational (normal progress)
- **Green** — success milestones
- **Red** — errors or warnings

**Cancel button** — Stops generation and returns to the input view.

Code generation can take 1–5 minutes for complex applications. If the log panel shows active messages, the system is working — the heartbeat keeps the progress indicator alive during the AI streaming phase.

---

## 8. Understanding the Success View

The success view shows:
- A green tick and "Application Deployed!" heading
- The application URL (`http://127.0.0.1:8001`)
- A **Copy** button to copy the URL
- An **Open in Browser** link
- A **Start New Generation** button

Your browser should have already opened automatically. If it did not, click **Open in Browser** or navigate manually to `http://127.0.0.1:8001`.

---

## 9. Stopping a Running Application

**From the Success view:** Click **Start New Generation** — stops the running application and resets to the input view.

The orchestrator automatically kills the previous generated application when a new generation starts.

---

## 10. Starting a New Generation

Click **Start New Generation** on the Success view (or reload the page). This stops the running app, closes WebSocket, and returns to the input view. Your API key configuration is preserved.

---

## 11. Common Errors and Fixes

### "Provider not configured"

You have not yet entered and validated your API key. Complete the **AI Provider Configuration** panel and click **Validate & Save**.

### "Invalid API key" / "Invalid Claude API key"

The API key was rejected. Common causes: copied with extra spaces, key revoked, wrong provider selected. Re-enter carefully and confirm the provider matches the key type.

### "Gemini rate limit exceeded"

The Gemini free tier allows 15 requests/minute and 1,500/day. Wait 60 seconds and retry. If the daily limit is exhausted, wait until midnight Pacific time (Google quota reset) or switch to a paid key.

### "Claude rate limit exceeded"

Wait 30–60 seconds then retry.

### "Invalid Minimax API key or wrong API endpoint"

A Minimax key must be obtained from `platform.minimax.io` and starts with `eyJ`. An `sk-...` key belongs to a different provider. If you want to use an OpenRouter key with Minimax-hosted models, use the **Custom** provider type instead.

### "No files were extracted from the AI response"

The AI did not format its response correctly. Click Cancel and retry. If it recurs, simplify the requirement.

### "generation timed out. Please retry."

The AI generation took longer than 10 minutes. This is unusual — retry the generation. If it happens consistently with a specific requirement, try simplifying or breaking it into smaller parts.

### "Server startup timed out after 30 seconds"

The generated application failed to start. Common causes: invalid `requirements.txt` package name, syntax error in `main.py`. Open `generated-apps/latest/` and inspect the files manually, or run `uvicorn main:app --port 8001` in that folder to see the error.

### "[Template warning] AI did not generate 'templates/index.html'"

The landing page template was missing from the AI's output. The generated app may show an empty or error page. Click Cancel, refine the plan to explicitly list all templates, and regenerate.

### "Base template not found"

The `base-template/` directory is missing. Run `setup.bat` or `setup.ps1` again.

---

## 12. Tips for Demonstrations

1. **Run setup the day before** — ensures venvs are built and no first-run delays.
2. **Pre-validate your API key** — opens the app and saves the config before the audience arrives.
3. **Prepare your requirement text in advance** — write it in a text file and copy-paste during the demo.
4. **Test the full flow once** — run one complete generation cycle to confirm everything works end to end.
5. **Keep the terminal visible on a second monitor** — the terminal log is reassuring to technical audiences.
6. **Choose a visually interesting requirement** — applications with data tables, cards, and colour produce more impressive demos.

---

## 13. Frequently Asked Questions

**Can I save a generated application permanently?**
Yes. Copy `generated-apps/latest/` to any location and run `uvicorn main:app --port 8001` from inside it (using its `.venv`).

**Can I edit the generated code?**
Yes. Open any file in `generated-apps/latest/` with a text editor. Restart uvicorn to see changes.

**What providers are supported?**
Four built-in: **Claude** (Anthropic), **Gemini** (Google), **Minimax**, and **Custom (OpenAI-compatible)**. The Custom option connects to any OpenAI-format provider — OpenAI, OpenRouter, Ollama, LM Studio, Azure OpenAI, Mistral, and others.

**Is my API key stored anywhere on disk?**
No. API keys are held only in process memory and discarded when the server stops.

**What happens if I close my browser during generation?**
The background task continues on the server. The app will still deploy. Reopen the browser at `http://127.0.0.1:8000` — status polling will pick up the current phase.

**Can I run this on Linux or macOS?**
Yes. Use `./setup.sh` and `./start.sh`. The application supports all platforms.

**Why does code generation take several minutes for complex apps?**
The AI generates up to 32,768 tokens of code in a single streaming call. Large multi-file applications with several templates and services take longer. The heartbeat keeps the UI progress indicator alive during this time.

**The generated app opens but shows errors or a blank page. What do I do?**
Go back, edit the plan to be more explicit about the requirements, and regenerate. You can also edit the files in `generated-apps/latest/` directly.

---

*Document maintained at `C:\planforaplan\docs\02-USER-GUIDE.md`*
