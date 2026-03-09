# AI Application Generator — User Guide

**Version:** 2.0  
**Date:** March 2026  
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

The AI Application Generator takes a plain English description of a web application and — within five minutes — produces a fully functional, locally-running Python web app that opens automatically in your browser.

The process works in two stages:

**Stage 1 — Plan:** You describe what you want. The AI generates a detailed implementation plan. You read it, edit it if needed, and approve it.

**Stage 2 — Generate and Deploy:** The AI writes all the code. The system copies it to a deployment folder, starts a local web server, and opens your browser at the running application.

You do not need to write any code, open a terminal, or install any additional tools once setup is complete.

---

## 2. Before You Begin

### Requirements

- **Python 3.11 or later** installed on your machine ([python.org](https://python.org))
- **An API key** for either Anthropic Claude or Minimax
- **Internet access** for AI API calls and for loading the Tailwind CSS stylesheet in generated apps
- The application has been set up (i.e. `setup.bat` has been run successfully)

### Getting an API Key

**Claude (Anthropic):**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign in and navigate to API Keys
3. Create a new key — it will start with `sk-ant-`

**Minimax:**
1. Visit [api.minimax.chat](https://api.minimax.chat)
2. Sign in and navigate to API Keys
3. Create a new key

Keep your API key private. Do not share it or paste it anywhere other than the configuration panel in this application.

---

## 3. Starting the Application

Open a Command Prompt window, navigate to the application folder, and run:

```
start.bat
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

The AI Application Generator interface will load. Leave the Command Prompt window open — the server runs there.

To stop the orchestrator, press **Ctrl+C** in the Command Prompt window.

---

## 4. Step-by-Step Workflow

### Step 1 — Configure the AI Provider

In the **AI Provider Configuration** panel at the bottom of the input page:

1. Select your provider from the dropdown: **Claude (Anthropic)** or **Minimax**.
2. Paste your API key into the **API Key** field.
3. Click **Validate & Save**.

Wait for the status message next to the button. If it shows a green tick and the provider name, configuration was successful. If it shows an error, check that you selected the correct provider and that the key is complete and unmodified.

You only need to do this once per session. The key is held in memory and will be cleared when you close the server.

### Step 2 — Describe Your Application

Click into the large text area at the top of the page and type a description of the web application you want to build.

Be specific about:
- What the application does
- What data it displays or manages
- Any interactive features you want

Example: `Build a to-do list application where users can add tasks, mark them as complete, and delete them. Show incomplete tasks highlighted in yellow.`

You can also click one of the example prompt buttons below the text area to populate the field with a starter requirement.

### Step 3 — Generate the Plan

Click the **Generate Plan** button.

The button will be disabled while the AI is working. This stage typically takes 15–30 seconds. You will then be taken to the Plan Review view.

### Step 4 — Review and Approve the Plan

The Plan view shows:
- Your original requirement on the left (read-only)
- The AI-generated implementation plan on the right (editable)

Read through the plan. If you want changes, edit the text directly in the right panel. Common edits include:
- Adding a feature the AI missed
- Removing a feature you do not need
- Clarifying the data structure or page layout

If you want the AI to completely regenerate the plan with refinements, click **↻ Regenerate Plan**.

When you are satisfied, click **Submit for Execution →**.

### Step 5 — Wait for Deployment

The Execution view shows a progress bar and a scrolling terminal log. You can watch each step:

1. AI generating application code
2. Parsing the generated files
3. Copying the base template
4. Writing generated files
5. Starting the application server
6. Launching your browser

This stage typically takes 60–120 seconds in total.

### Step 6 — Use Your Application

When deployment is complete, your browser will automatically open at `http://127.0.0.1:8001` showing the generated application.

The Success view also shows the URL and a copy button if you need to share the link.

---

## 5. Writing Effective Requirements

The quality of the generated application depends heavily on the clarity and specificity of your requirement. These guidelines will help.

### Be Specific About Features

| Vague | Better |
|-------|--------|
| "Make a shopping app" | "Build a product catalogue with a list of items, each showing name, price, and a short description. Include a search bar to filter by name." |
| "A dashboard" | "Create a data dashboard showing four summary cards: total sales, average order value, number of customers, and top product. Use placeholder data." |

### State the Visual Style if It Matters

If you want a specific look, include it: "Use a clean minimalist design with a white background and blue accent colour" or "Dark theme with a sidebar navigation."

### Mention Data if Relevant

If the app needs data, say so: "Use hardcoded sample data for five products" or "Use a JSON file to store tasks."

### Exclude What You Do Not Need

"Do not include user authentication" or "No database required — just in-memory storage for this demo."

### Aim for 50–200 Words

Short requirements produce minimal applications. Detailed requirements (100–200 words) produce richer results. Requirements over 300 words may exceed the token context for the plan stage.

---

## 6. Understanding the Plan View

The plan is a markdown document structured with headings for:

- **File Structure** — every file the AI intends to create
- **Component Breakdown** — what each file does
- **Technical Approach** — libraries, data flow, URL structure
- **Implementation Steps** — the build order

You are encouraged to read it and edit freely. The plan is passed directly to Stage 2 as instructions, so any changes you make will influence what gets built.

If the plan looks completely wrong (for example, it suggests a database when you asked for a simple static page), click **Regenerate Plan** to get a fresh attempt.

---

## 7. Understanding the Execution View

The execution view has three elements:

**Phase label and percentage** — Shows the current step and overall progress from 0% to 100%.

**Terminal log panel** — A scrolling dark panel showing real-time messages from the system. Lines are colour-coded:
- **White/grey** — informational messages (normal progress)
- **Green** — success milestones
- **Red** — errors

**Cancel button** — Stops the current generation and returns you to the input view. Use this if you see persistent errors or want to start over.

Progress updates every 1.5 seconds. If the log panel is scrolling actively, the system is working.

---

## 8. Understanding the Success View

The success view confirms your application is running and shows:

- A green tick and "Application Deployed!" heading
- The application URL (`http://127.0.0.1:8001`)
- A **Copy** button to copy the URL to your clipboard
- An **Open in Browser** link that opens a new tab
- A **Start New Generation** button

Your browser should have already opened automatically at the application URL. If it did not, click **Open in Browser** or manually navigate to `http://127.0.0.1:8001`.

---

## 9. Stopping a Running Application

The generated application runs on port 8001. There are two ways to stop it:

**From the Success view:** Click **Start New Generation** — this stops the running application and resets to the input view.

**From any view:** Click the **■ Cancel** button in the Execution view, or reload the page and use the browser's Stop button.

The orchestrator automatically kills the previous generated application when a new generation starts, so you do not need to manually stop it before generating again.

---

## 10. Starting a New Generation

Click **Start New Generation** on the Success view (or reload the page). This:
- Stops the currently running generated application
- Closes the WebSocket connection
- Returns to the input view
- Clears the progress and log panel

Your API key configuration is preserved for the rest of the session.

---

## 11. Common Errors and Fixes

### "Provider not configured"

You have not yet entered and validated your API key. Go back to the input view and complete the **AI Provider Configuration** panel.

### "Invalid API key"

The API key was rejected by the provider. Common causes:
- The key was copied with extra spaces
- The key has been revoked
- You selected the wrong provider (e.g., entered a Claude key with Minimax selected)

Solution: Re-enter the key carefully. Make sure the provider dropdown matches the key.

### "Claude rate limit exceeded. Please wait and retry."

Your account has hit the API rate limit. Wait 30–60 seconds then try again.

### "No files were extracted from the AI response"

The AI did not format its response correctly using the required XML file blocks. This occasionally happens with complex requirements. Solution: Click Cancel and try again. If it recurs, simplify the requirement.

### "Server startup timed out after 30 seconds"

The generated application failed to start within 30 seconds. Common causes:
- The generated `requirements.txt` contains an invalid package name
- The generated `main.py` has a syntax error

Solution: Open the deployment folder (`generated-apps/latest/`) and inspect `main.py` and `requirements.txt` manually. You can also run `uvicorn main:app --port 8001` in that folder to see the startup error directly.

### "Base template not found"

The `base-template/` directory is missing or the `setup.bat` script was not run, or it failed. Solution: Run `setup.bat` again.

### The generated application opens but shows errors

The AI occasionally generates code with minor bugs. You can:
- Edit the files in `generated-apps/latest/` directly and restart uvicorn
- Return to the Plan view, edit the plan to clarify the requirement, and regenerate

---

## 12. Tips for Demonstrations

For a five-minute live demonstration, the following preparation helps significantly:

1. **Run setup.bat the day before** — Ensure all dependencies are installed and the base template venv is built. This avoids first-run delays.

2. **Pre-validate your API key** — Open the application and validate your key before the audience arrives. This confirms the key works and saves 10–15 seconds during the demo.

3. **Prepare your requirement text in advance** — Write a clear, tested requirement in a text file. Copy and paste it during the demo to avoid typing errors under pressure.

4. **Test the full flow once before the demonstration** — Run one complete generation cycle to confirm everything works end to end on the demo machine.

5. **Keep the terminal visible on a second monitor** — The terminal shows real-time progress and is reassuring to a technical audience.

6. **Choose a visually interesting requirement** — Applications with data tables, cards, and colour produce more impressive demos than plain text lists.

---

## 13. Frequently Asked Questions

**Can I save a generated application permanently?**  
Yes. The generated files are in `generated-apps/latest/`. Copy this folder to any location and run `uvicorn main:app --port 8001` from inside it (using its `.venv`).

**Can I edit the generated code?**  
Yes. Open any file in `generated-apps/latest/` with a text editor. If you change `main.py` or a template, restart uvicorn to see the changes.

**Can I generate multiple applications?**  
One at a time. Each generation replaces the previous one in `generated-apps/latest/`. Rename the folder if you want to preserve a previous result.

**Does the generated application persist after I close the orchestrator?**  
The files on disk persist. The uvicorn subprocess that serves the app is terminated when you click Stop or close the orchestrator. Restart it manually from the deployment folder.

**Can I use a different AI provider for different generations?**  
Yes. Go back to the input view, update the provider and key in the configuration panel, click Validate & Save, then proceed with a new generation.

**Is my API key stored anywhere on disk?**  
No. API keys are held only in process memory and are discarded when the orchestrator server is stopped. They are never written to disk, log files, or any other persistent storage.

**What happens if I close my browser during generation?**  
The background task continues to run on the server. The generated application will still be deployed. When you reopen the browser and navigate to `http://127.0.0.1:8000`, the status polling will pick up the current phase.

**Can I run this on Linux or macOS?**  
The application code supports all platforms. The `setup.bat` and `start.bat` scripts are Windows-only. On Linux or macOS, create a virtual environment with `python3 -m venv .venv`, activate it, install with `pip install -e ".[dev]"`, do the same for `base-template/`, then run `uvicorn app.main:app --host 127.0.0.1 --port 8000`.

---

*Document maintained at `C:\saabdemo\app\docs\02-USER-GUIDE.md`*
