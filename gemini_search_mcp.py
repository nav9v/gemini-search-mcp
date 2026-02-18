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
from mcp.types import Tool, TextContent
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
