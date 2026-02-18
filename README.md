# Gemini MCP Server: Free AI Search & Grounding for VS Code

> **Open-source Perplexity alternative** for developers. Connect VS Code Copilot, Cline, or Roo to **Google Search** and **Deep Web Analysis** via the Model Context Protocol (MCP).

[![MCP Badge](https://lobehub.com/badge/mcp/nav9v-gemini-mcp-server)](https://lobehub.com/mcp/nav9v-gemini-mcp-server)
[![MCP Compatible](https://img.shields.io/badge/MCP-compatible-green?style=flat-square)](https://modelcontextprotocol.io/)
[![Gemini API](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Free Tier](https://img.shields.io/badge/Cost-Free_(1500%2Fday)-brightgreen?style=flat-square)](https://ai.google.dev/gemini-api/docs/pricing)

---

## 📖 Table of Contents
- [Why use this?](#why-use-this-gemini-mcp-server)
- [How it Works](#how-it-works-grounding-architecture)
- [Key Features](#key-features)
- [Available Tools](#available-tools)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Comparison](#how-is-this-different-from-other-mcp-search-servers)
- [Troubleshooting](#troubleshooting)

---

## Why use this Gemini MCP Server?

This is a **Model Context Protocol (MCP) server** that upgrades your AI coding assistant (like **VS Code GitHub Copilot**, Cline, or Roo Code). It provides real-time Internet access and deep web page analysis using **Google's Gemini 2.5 Flash API**.

It uses **Google Search Grounding**, allowing your LLM to fetch factual answers from the web without hallucinating.

**Benefits:**
*   **Perplexity in your IDE:** Ask "What is the latest Next.js 15 breaking change?" and get a cited answer without leaving VS Code.
*   **Free to run:** Uses the Google AI Studio free tier (**1,500 requests/day**).
*   **Deep Context:** Doesn't just read snippets; it uses Gemini's `url_context` to read full documentation pages, PDFs, and technical blogs.

### How it Works (Grounding Architecture)

```mermaid
graph LR
    A[User in VS Code] -->|Asks Question| B(Copilot / MCP Client);
    B -->|Routes Query| C[Gemini MCP Server];
    C -->|API Call| D[Gemini API];
    D -->|1. Search & Retrieve| E[Google Search / Web Index];
    D -->|2. Augment Context| D;
    D -->|3. Generate Answer| B;
    B -->|Final Answer| A;
```

---

## Key Features

- 🔍 **Grounding with Google Search:** Uses the official [Google Search Grounding](https://ai.google.dev/gemini-api/docs/google-search) for factual, up-to-date results.
- 📄 **Deep URL Analysis:** Uses Gemini's [URL Context](https://ai.google.dev/gemini-api/docs/url-context) to read large documents (HTML, PDF) for summarization and QA.
- 📚 **Citations & Sources:** Every claim is backed by a clickable link, distinguishing it from standard LLM hallucinations.
- 🎯 **Pre-configured Prompts:** Ready-to-use templates for common research and analysis tasks.
- 📊 **Resource Access:** Query server capabilities and information dynamically.
- ✅ **Standard MCP Protocol:** Compatible with any MCP client, including **Cursor**, **Windsurf**, and **VS Code**.
- ⚡ **Low Latency:** Powered by `gemini-2.5-flash`, optimized for speed and low cost.
- 🆓 **100% Free Tier:** Works with the free Google AI Studio API key (no credit card required).

---

## Available Tools

| Tool | Description | Use Case |
|---|---|---|
| `search` | **AI Web Search.** Searches Google and summarizes results using Gemini. Returns sources. | "How do I center a div in Tailwind 4?" or "Latest features in Python 3.13" |
| `analyze_url` | **Deep Page Reader.** Ingests the content of a specific URL (HTML/PDF/Text) into context. | "Read this documentation page and explain the implementation details." |

## Available Prompts

Pre-configured prompts to make common tasks easier:

| Prompt | Description | Arguments |
|---|---|---|
| `web-search` | Search the web for up-to-date information | `topic` (required) |
| `analyze-documentation` | Analyze and summarize technical documentation | `url` (required), `focus` (optional) |
| `research-topic` | Comprehensive research with multiple sources | `topic` (required) |
| `compare-technologies` | Compare technologies/frameworks/tools | `technologies` (required), `criteria` (optional) |

## Available Resources

| Resource | URI | Description |
|---|---|---|
| Server Information | `gemini://server/info` | Details about the server version and capabilities |
| Server Capabilities | `gemini://server/capabilities` | JSON of all features, tools, and limits |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/nav9v/gemini-search-mcp.git
cd gemini-mcp-server
```

### 2. Set up the Python environment

```powershell
python -m venv .venv
# Activate virtual environment
# Windows:
.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

<details>
<summary>💡 PowerShell execution policy error?</summary>

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
</details>

### 3. Get your Free API Key

1.  Go to [Google AI Studio](https://aistudio.google.com/apikey).
2.  Create a **free API key** (no credit card needed).
3.  Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 4. Add to VS Code

Edit your MCP config file:
*   **Windows:** `%APPDATA%\Code\User\mcp.json`
*   **Mac/Linux:** `~/Library/Application Support/Code/User/mcp.json`

**Option 1: Using working directory (Recommended)**
```json
{
  "mcpServers": {
    "gemini-search": {
      "command": "python",
      "args": ["gemini_search_mcp.py"],
      "cwd": "C:/absolute/path/to/gemini-search-mcp",
      "env": {
        "PYTHONPATH": "C:/absolute/path/to/gemini-search-mcp"
      }
    }
  }
}
```

**Option 2: Using virtual environment**
```json
{
  "mcpServers": {
    "gemini-search": {
      "command": "C:/absolute/path/to/.venv/Scripts/python.exe",
      "args": ["C:/absolute/path/to/gemini_search_mcp.py"]
    }
  }
}
```

> **Note:** 
> - Replace `C:/absolute/path/to/` with the full path to your cloned folder
> - Use forward slashes (`/`) or double backslashes (`\\`) in paths
> - The server loads `.env` automatically, so you don't need the `env` block if using `.env`
> - See [mcp.json.example](mcp.json.example) for a template

### 5. Reload VS Code

Press `Ctrl+Shift+P` → **Developer: Reload Window**.

---

## 💬 Usage Examples

### Using Tools Directly

Open **Copilot Chat** (or your MCP client) and ask:

*   **"Search for the latest Next.js 15 breaking changes."** (Triggers `search`)
*   **"Analyze this page: https://docs.python.org/3/whatsnew/3.13.html"** (Triggers `analyze_url`)
*   **"What are the best open source alternatives to Vercel in 2026?"**
*   **"Read the docs at https://fastapi.tiangolo.com/ and explain how to use dependency injection."**

### Using Prompts (Recommended)

Prompts provide structured templates for common tasks:

*   **Web Search:** Use the `web-search` prompt with a topic
*   **Documentation Analysis:** Use the `analyze-documentation` prompt with a URL
*   **Research:** Use the `research-topic` prompt for comprehensive research
*   **Comparison:** Use the `compare-technologies` prompt to compare tools/frameworks

Example in VS Code Copilot:
```
@gemini-search #web-search topic="Python async best practices 2026"
```

---

## Configuration

All config is via `.env` in the project root:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Google AI Studio API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |

### Supported Models

| Model | Status | Cost | Best For |
|---|---|---|---|
| `gemini-2.5-flash` | ✅ Stable | Free | **General Use** — fast, free tier, accurate. |
| `gemini-2.5-flash-lite` | ✅ Stable | Free | Ultra-fast simple queries. |
| `gemini-2.5-pro` | ✅ Stable | Paid* | Complex reasoning & research planning. |
| `gemini-2.0-flash-thinking` | 🧪 Preview | Free | Deep reasoning tasks. |

*\*Paid after free tier limits.*

---

## 💰 Pricing

**Completely Free.**
1.  **Google AI Studio API:** Free tier includes **1,500 requests per day**.
2.  **This Software:** Open source (MIT).

No credit card required. Perfect for individual developers, students, and prototypers.

---

## 🆚 Comparison

| Feature | This Server | Brave Search MCP | Tavily / Serper | Perplexity |
|---|---|---|---|---|
| **Engine** | **Google** (Grounding) | Brave Index | Tavily Index | Perplexity |
| **Full Page Read** | ✅ **Yes** (huge context) | ❌ No | ❌ No | ❌ No |
| **Citations** | ✅ Inline Links | ✅ | ✅ | ✅ |
| **Prompts** | ✅ **4 Pre-configured** | ❌ No | ❌ No | ❌ No |
| **Resources** | ✅ **Server Info** | ❌ No | ❌ No | N/A |
| **Cost** | 🆓 **Free** (1.5k/day) | 🆓 Limited | 🆓 Limited | 💸 $20/mo |
| **Privacy** | 🔒 Local Client* | 🔒 Local Client | ☁️ API | ☁️ API |

*\*Runs locally, sends queries to Google Gemini API.*

---

## 🛠 Troubleshooting

<details>
<summary><strong>Test Server Manually</strong></summary>

Before configuring VS Code, test the server directly:

```powershell
# Activate virtual environment first
.venv\Scripts\Activate.ps1

# Run the server
python gemini_search_mcp.py
```

The server should start without errors. Press `Ctrl+C` to stop.
</details>

<details>
<summary><strong>Verify Installation</strong></summary>

1.  Open VS Code Output panel (`Ctrl+Shift+U`).
2.  Select **"MCP Review"** or **"Github Copilot Default"** from the dropdown.
3.  Look for `gemini-search` in the logs.
4.  Check for any error messages or connection issues.
</details>

<details>
<summary><strong>"GEMINI_API_KEY is not set"</strong></summary>

- Ensure `.env` is in the **same folder** as the script.
- Verify the path in `mcp.json` is absolute: `c:/Users/.../gemini-search-mcp/gemini_search_mcp.py`.
- Check that `.env` contains a valid API key without quotes or spaces.
- Test locally: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GEMINI_API_KEY'))"`
</details>

<details>
<summary><strong>Server Not Appearing in VS Code</strong></summary>

1.  Verify `mcp.json` syntax is valid (use a JSON validator).
2.  Ensure paths use forward slashes or double backslashes.
3.  Check that Python is accessible from the command line: `python --version`
4.  Try using absolute path to Python executable in virtual environment.
5.  Reload VS Code window: `Ctrl+Shift+P` → **Developer: Reload Window**
</details>

<details>
<summary><strong>Validation Failed</strong></summary>

If the MCP server validation fails:

1.  Ensure all dependencies are installed: `pip install -r requirements.txt`
2.  Check that the `google-genai` package is properly installed: `pip show google-genai`
3.  Verify your API key is valid at [Google AI Studio](https://aistudio.google.com/apikey)
4.  Test the server manually before adding to VS Code
5.  Check that prompts and resources are properly defined (this MCP server includes them)
</details>

---

## Contributing

Pull requests are welcome! Please format code with `black` and ensure strict typing.

## License

[MIT](LICENSE) © 2026 Navneet Sharma

---

<!-- SEO Keywords -->
<details>
<summary><i>Keywords</i></summary>
VS Code Extension, Model Context Protocol, MCP Server, Gemini API, Google Search Grounding, RAG, Retrieval Augmented Generation, Perplexity Alternative, Open Source AI, Copilot Tools, Cline, Roo Code, AI Search, Python, Deep Research.
</details>
