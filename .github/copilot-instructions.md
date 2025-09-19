# BrowserPilot - GitHub Copilot Instructions

## Project Overview
BrowserPilot is an AI-powered browser automation tool that uses computer vision to navigate and interact with websites intelligently. The system combines browser automation, proxy management, anti-bot detection, and AI vision to accomplish web scraping and automation tasks through natural language commands.

## Architecture
- **Backend**: Python FastAPI application with async/await patterns
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS
- **Core Technologies**: Playwright for browser automation, Google Gemini AI for vision processing
- **Key Components**: Smart browser controller, proxy management, anti-bot detection, universal content extraction

## Technology Stack & Standards

### Backend (Python)
- **Framework**: FastAPI with async/await patterns
- **Python Version**: 3.8+
- **Key Dependencies**: 
  - `playwright` for browser automation
  - `google-generativeai` for AI vision processing
  - `fastapi` and `uvicorn` for web server
  - `pydantic` for data validation
- **Code Style**: 
  - Use async/await for all I/O operations
  - Type hints are encouraged but not always required
  - Use descriptive variable names and docstrings
  - Follow PEP 8 naming conventions
- **Error Handling**: Always include comprehensive try/catch blocks for browser operations and external API calls

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React hooks (useState, useEffect)
- **Code Style**:
  - Use functional components with hooks
  - TypeScript interfaces for props and data structures
  - Descriptive component and variable names
  - Tailwind utility classes for styling

## Key Concepts & Patterns

### Browser Automation
- All browser interactions go through `SmartBrowserController`
- Always handle timeouts and failures gracefully
- Use vision-based element detection rather than rigid selectors
- Implement retry logic for unreliable operations

### Proxy Management
- Proxies are managed through `SmartProxyManager`
- Auto-rotation on detection or blocking
- Health tracking and performance-based selection
- Site-specific blocking lists

### AI Vision Integration
- Google Gemini AI processes screenshots for decision making
- Universal system prompts work across any website type
- Always include reasoning in AI responses
- Format responses as JSON with action and reason fields

### Content Extraction
- Support multiple output formats: txt, md, json, html, csv, pdf
- Format detection from natural language prompts
- Automatic format conversion and file generation
- Metadata preservation and timestamping

## Development Guidelines

### When Adding New Features
1. **Browser Operations**: Always wrap in try/catch blocks and implement retries
2. **AI Integration**: Include clear prompts and validate response formats
3. **File Operations**: Use Path objects and ensure directory creation
4. **API Endpoints**: Follow FastAPI patterns with proper type hints and error responses
5. **Frontend Components**: Use TypeScript interfaces and handle loading/error states

### Code Patterns to Follow

#### Backend API Endpoints
```python
@app.post("/endpoint")
async def endpoint_name(req: RequestModel):
    try:
        # Validate input
        # Process request with proper async/await
        # Return structured response
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### Browser Controller Operations
```python
async def perform_action(self, action_data: dict):
    for attempt in range(self.max_retries):
        try:
            # Perform browser action
            await self.page.some_action()
            return True
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == self.max_retries - 1:
                raise
            await asyncio.sleep(2)
```

#### React Components
```typescript
interface ComponentProps {
  data: DataType;
  onAction: (action: string) => void;
}

export const Component: React.FC<ComponentProps> = ({ data, onAction }) => {
  const [loading, setLoading] = useState(false);
  
  const handleAction = async () => {
    setLoading(true);
    try {
      await onAction('action');
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Component content */}
    </div>
  );
};
```

### File and Directory Structure
- **Backend modules**: Keep focused on single responsibilities
- **Frontend components**: One component per file, co-locate related types
- **Configuration**: Use environment variables for secrets and settings
- **Output files**: All generated content goes in `outputs/` directory
- **Logs**: Include structured logging with emojis for visual clarity

### Testing Approach
- No formal test infrastructure exists yet
- Manual testing through the web interface
- Test with various website types and scenarios
- Validate all supported output formats
- Test proxy rotation and anti-bot detection

## Common Tasks & Patterns

### Adding a New Output Format
1. Update `detect_format_from_prompt()` in `agent.py`
2. Add format handling in `save_content()` function
3. Update frontend format selector in `JobForm.tsx`
4. Test format detection and file generation

### Enhancing AI Vision Processing
1. Modify prompts in `vision_model.py`
2. Update decision processing in `agent.py`
3. Test with various website types
4. Validate JSON response formats

### Adding New Browser Automation Features
1. Extend `SmartBrowserController` class
2. Add error handling and retries
3. Integrate with existing proxy rotation
4. Update agent decision-making logic

## Debugging & Troubleshooting
- **Browser Issues**: Check proxy health and rotation status
- **AI Failures**: Validate API key and response formats
- **File Operations**: Ensure output directory exists and permissions
- **WebSocket Issues**: Check connection status and error handling
- **Frontend Issues**: Check browser console and network tab

## Security Considerations
- Environment variables for API keys and sensitive data
- Proxy credentials handled securely
- No direct file system access from frontend
- Input validation on all endpoints
- Safe file naming and path handling

## Performance Optimization
- Efficient screenshot processing and caching
- Smart proxy selection based on performance metrics
- Async operations to prevent blocking
- Resource cleanup after browser sessions
- Minimal screenshot data transfer