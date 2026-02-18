# Changelog

All notable changes to the Gemini Search MCP Server will be documented in this file.

## [1.1.0] - 2026-02-18

### Added
- **Prompts Support**: Added 4 pre-configured prompts for common use cases:
  - `web-search`: Search the web for up-to-date information
  - `analyze-documentation`: Analyze and summarize technical documentation
  - `research-topic`: Comprehensive research with multiple sources
  - `compare-technologies`: Compare technologies, frameworks, or tools
  
- **Resources Support**: Added 2 resources for server introspection:
  - `gemini://server/info`: Server version and status information
  - `gemini://server/capabilities`: JSON of all features, tools, and limits

- **Better Documentation**: 
  - Added detailed usage examples for prompts
  - Improved installation instructions with multiple configuration options
  - Added comprehensive troubleshooting section
  - Created `mcp.json.example` for easy configuration

### Changed
- Updated `mcp.json` to use working directory (`cwd`) instead of absolute paths for better portability
- Enhanced README with comparison table highlighting new features
- Improved error handling and validation instructions

### Fixed
- Configuration path issues for cross-platform compatibility
- Validation requirements now met with prompts and resources

---

## [1.0.0] - 2026-01-XX

### Initial Release
- Basic web search tool using Google Search grounding
- URL analysis tool for deep content reading
- Support for Gemini 2.5 Flash model
- Citations and source tracking
- Free tier support (1,500 requests/day)
