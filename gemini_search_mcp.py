"""Gemini Search MCP Server — Google Search + URL Context grounding for VS Code."""

import asyncio
import os
import re
import sys
import logging
from pathlib import Path

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Prompt, PromptMessage, Resource
from google import genai
from google.genai.types import GenerateContentConfig

load_dotenv(Path(__file__).resolve().parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY is not set.", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)
log = logging.getLogger("gemini-search")

client = genai.Client(api_key=GEMINI_API_KEY)
app = Server("gemini-search")


def _extract_text(response) -> str:
    try:
        return "".join(
            part.text for part in response.candidates[0].content.parts
            if hasattr(part, "text") and part.text
        )
    except (IndexError, AttributeError):
        return ""


def _extract_sources(response) -> str:
    try:
        metadata = getattr(response.candidates[0], "grounding_metadata", None)
        if not metadata:
            return ""
        chunks = getattr(metadata, "grounding_chunks", None)
        if not chunks:
            return ""
        lines, seen = [], set()
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            if web and web.uri and web.uri not in seen:
                seen.add(web.uri)
                lines.append(f"- [{web.title or web.uri}]({web.uri})")
        return "\n\n## Sources\n" + "\n".join(lines) if lines else ""
    except Exception as exc:
        log.warning("Could not extract sources: %s", exc)
        return ""


def _extract_url_metadata(response) -> str:
    try:
        metadata = getattr(response.candidates[0], "url_context_metadata", None)
        if not metadata:
            return ""
        url_metadata = getattr(metadata, "url_metadata", None)
        if not url_metadata:
            return ""
        lines = [
            f"- `{getattr(e, 'retrieved_url', 'unknown')}` — {getattr(e, 'url_retrieval_status', 'unknown')}"
            for e in url_metadata
        ]
        return "\n\n## URL Retrieval Status\n" + "\n".join(lines) if lines else ""
    except Exception as exc:
        log.warning("Could not extract URL metadata: %s", exc)
        return ""


def _is_valid_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", url.strip()))


TOOLS = [
    Tool(
        name="search",
        description=(
            "Search the web with Gemini + Google Search grounding. "
            "Returns cited, summarized answers like Perplexity. "
            "Automatically fetches and analyzes full webpage content via url_context. "
            "Use this tool when you need to find up-to-date information, answer factual "
            "questions, research topics, or discover resources on the web. "
            "Do NOT use this for analyzing a specific known URL — use analyze_url instead."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What to search for. Can be a question or topic.",
                }
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="analyze_url",
        description=(
            "Deeply analyze the content of a specific webpage. "
            "Goes beyond search snippets to ingest complete page content. "
            "Use this tool when you already have a URL and want to extract, "
            "summarize, or ask questions about its content. "
            "Supports HTML, PDF, JSON, plain text, images, and more (up to 34 MB). "
            "Do NOT use this for general web search — use search instead."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to analyze",
                },
                "question": {
                    "type": "string",
                    "description": "Optional: Specific question about the URL content",
                },
            },
            "required": ["url"],
        },
    ),
]

PROMPTS = [
    Prompt(
        name="web-search",
        description="Search the web for up-to-date information on any topic",
        arguments=[
            {
                "name": "topic",
                "description": "The topic or question to search for",
                "required": True
            }
        ]
    ),
    Prompt(
        name="analyze-documentation",
        description="Analyze and summarize technical documentation from a URL",
        arguments=[
            {
                "name": "url",
                "description": "The URL of the documentation to analyze",
                "required": True
            },
            {
                "name": "focus",
                "description": "Optional: Specific aspect to focus on (e.g., 'API usage', 'installation steps')",
                "required": False
            }
        ]
    ),
    Prompt(
        name="research-topic",
        description="Perform comprehensive research on a technical topic with multiple sources",
        arguments=[
            {
                "name": "topic",
                "description": "The technical topic to research",
                "required": True
            }
        ]
    ),
    Prompt(
        name="compare-technologies",
        description="Compare two or more technologies, frameworks, or tools",
        arguments=[
            {
                "name": "technologies",
                "description": "Comma-separated list of technologies to compare (e.g., 'React, Vue, Svelte')",
                "required": True
            },
            {
                "name": "criteria",
                "description": "Optional: Specific criteria to compare (e.g., 'performance, learning curve, ecosystem')",
                "required": False
            }
        ]
    ),
]

RESOURCES = [
    Resource(
        uri="gemini://server/info",
        name="Server Information",
        description="Information about this Gemini Search MCP server",
        mimeType="text/plain"
    ),
    Resource(
        uri="gemini://server/capabilities",
        name="Server Capabilities",
        description="Available tools and features of this server",
        mimeType="application/json"
    ),
]


@app.list_tools()
async def list_tools():
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search":
        return await _handle_search(arguments)
    elif name == "analyze_url":
        return await _handle_analyze_url(arguments)
    return [TextContent(type="text", text=f"Unknown tool: {name}")]


@app.list_prompts()
async def list_prompts():
    return PROMPTS


@app.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "web-search":
        topic = arguments.get("topic", "")
        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Search the web for information about: {topic}\n\n"
                     f"Please provide a comprehensive answer with sources and citations."
            )
        )
    elif name == "analyze-documentation":
        url = arguments.get("url", "")
        focus = arguments.get("focus", "")
        focus_text = f" Focus specifically on: {focus}" if focus else ""
        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Analyze the documentation at: {url}\n\n"
                     f"Provide a clear summary of the key points, implementation details, and best practices.{focus_text}"
            )
        )
    elif name == "research-topic":
        topic = arguments.get("topic", "")
        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Conduct comprehensive research on: {topic}\n\n"
                     f"Include: current state, best practices, pros/cons, recommendations, and authoritative sources."
            )
        )
    elif name == "compare-technologies":
        technologies = arguments.get("technologies", "")
        criteria = arguments.get("criteria", "performance, ease of use, ecosystem, learning curve")
        return PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=f"Compare the following technologies: {technologies}\n\n"
                     f"Comparison criteria: {criteria}\n\n"
                     f"Provide an objective comparison with sources and practical recommendations."
            )
        )
    return PromptMessage(
        role="user",
        content=TextContent(type="text", text=f"Unknown prompt: {name}")
    )


@app.list_resources()
async def list_resources():
    return RESOURCES


@app.read_resource()
async def read_resource(uri: str):
    if uri == "gemini://server/info":
        info_text = f"""Gemini Search MCP Server
Version: 1.0.0
Model: {GEMINI_MODEL}
Status: Active

This server provides AI-powered web search and URL analysis using Google's Gemini API.

Available Tools:
- search: Search the web with Google Search grounding
- analyze_url: Deep analysis of webpage content

Features:
- Real-time web search with citations
- Full webpage content analysis (HTML, PDF, etc.)
- Powered by Gemini 2.5 Flash
- Free tier: 1,500 requests/day
"""
        return TextContent(type="text", text=info_text)
    
    elif uri == "gemini://server/capabilities":
        import json
        capabilities = {
            "server": "gemini-search",
            "version": "1.0.0",
            "model": GEMINI_MODEL,
            "tools": ["search", "analyze_url"],
            "prompts": ["web-search", "analyze-documentation", "research-topic", "compare-technologies"],
            "features": {
                "google_search_grounding": True,
                "url_context_analysis": True,
                "citations": True,
                "free_tier": True
            },
            "limits": {
                "requests_per_day": 1500,
                "max_url_size_mb": 34
            }
        }
        return TextContent(type="text", text=json.dumps(capabilities, indent=2))
    
    return TextContent(type="text", text=f"Unknown resource: {uri}")


async def _handle_search(arguments: dict) -> list[TextContent]:
    query = (arguments.get("query") or "").strip()
    if not query:
        return [TextContent(type="text", text="Error: query is required and cannot be empty.")]

    log.info("search | query=%s | model=%s", query, GEMINI_MODEL)
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=query,
            config=GenerateContentConfig(
                tools=[{"google_search": {}}, {"url_context": {}}],
            ),
        )
        answer = _extract_text(response)
        if not answer:
            return [TextContent(type="text", text="No results found for the query.")]
        return [TextContent(type="text", text=answer + _extract_sources(response))]
    except Exception as exc:
        log.error("search failed: %s", exc)
        return [TextContent(type="text", text=f"Error performing search: {exc}")]


async def _handle_analyze_url(arguments: dict) -> list[TextContent]:
    url = (arguments.get("url") or "").strip()
    question = (arguments.get("question") or "").strip()

    if not url:
        return [TextContent(type="text", text="Error: url is required and cannot be empty.")]
    if not _is_valid_url(url):
        return [TextContent(type="text", text=f"Error: Invalid URL format: {url}")]

    prompt = (question or "Analyze and summarize the content of this page.") + f"\n\nURL: {url}"
    log.info("analyze_url | url=%s | model=%s", url, GEMINI_MODEL)

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=GenerateContentConfig(tools=[{"url_context": {}}]),
        )
        answer = _extract_text(response)
        if not answer:
            return [TextContent(type="text", text=f"Could not retrieve content from {url}.")]
        return [TextContent(type="text", text=f"# Analysis of {url}\n\n{answer}{_extract_url_metadata(response)}")]
    except Exception as exc:
        log.error("analyze_url failed: %s", exc)
        return [TextContent(type="text", text=f"Error analyzing URL: {exc}")]


async def main():
    log.info("Starting Gemini MCP server (model=%s)", GEMINI_MODEL)
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
