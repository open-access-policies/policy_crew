# Policy Crew Codebase Guidelines

## Project Overview

You are building an AI-powered Information Security Management System (ISMS) generator using CrewAI. This system will create comprehensive, tailored security policies and procedures in a Jekyll-ready format for deployment via GitHub Pages.

### Core Architecture

The system uses a **file-based workflow** where:
- All agent interactions are mediated through Markdown files stored in a `notes/` directory
- Generated policies are saved directly to their target directory structure
- Each agent has a specific role and expertise area
- The workflow is orchestrated by a conductor agent that manages review cycles

### Key Design Principles

1. **Quality over Speed**: Optimize for output quality, not execution time
2. **Iterative Review**: Multiple specialist agents review and improve each policy
3. **File-Based Persistence**: All work products saved as Markdown files
4. **Modular Architecture**: Easily swap backend models (Ollama) or agents
5. **Test-Driven Development**: Comprehensive testing at each step
6. **Incremental Progress**: Small, safe steps that build on each other
7. **Agent-Driven Quality Assessment**: Content readability and testability evaluated by agents, not automated code

### Technology Stack

- **Framework**: CrewAI for agent orchestration
- **Models**: Ollama for local LLM hosting (adaptable backend)
- **Output Format**: Jekyll-compatible Markdown with YAML front matter
- **File System**: Structured directory layout matching Jekyll conventions
- **Testing**: Pytest for unit/integration testing, file system validation

### Agent Ecosystem

The system includes 12 specialized agents:
- **Interviewer**: Gathers requirements and creates project brief
- **Policy Architect**: Designs overall ISMS structure and policy map
- **Writer**: Drafts initial policies and procedures
- **5 Reviewers**: Adversarial, CTO, Compliance, Legal, Operational Impact
- **Conductor**: Orchestrates review cycles and quality gates
- **Executive Editor**: Final polish and consistency
- **Governance Specialist**: Creates implementation roadmaps
- **HR Writer**: People-focused policies
- **Trust & Safety**: Platform-specific policies

## Build, Lint, Test Commands
- Build: `python -m pip install -r requirements.txt` (if applicable)
- Lint: `ruff check .` or `flake8 .`
- Test: `pytest` or `python -m pytest`
- Run single test: `pytest tests/test_file.py::test_function_name`

## Code Style Guidelines
- Python 3.9+ with PEP8 style guide
- Use f-strings for string formatting
- Type hints for all function parameters and return values
- Imports grouped in: standard library, third-party, local
- Class names use PascalCase, function names use snake_case
- Constants in UPPER_CASE
- Error handling with try/except blocks for file operations
- Comprehensive docstrings using Google style format

## Testing Approach
- Test-driven development with pytest
- Mock external dependencies (Ollama)
- File system validation tests
- Integration tests for agent workflows
- Property-based testing for file generation

## Interviewer Agent Usage
To run the interactive interviewer agent:
1. Ensure Ollama is running with the phi3 model available
2. Run `python src/interviewer_agent.py` to start an interactive interview session
3. The agent will generate questions and collect responses
4. Type "done" or "finish" when complete to save the structured JSON output

## Coding Guidelines

### Error Handling
- Always use try/catch blocks for file operations
- Validate file paths and permissions before operations
- Graceful degradation when agents fail
- Comprehensive logging for debugging

### File Operations
- Use absolute paths consistently
- Atomic file writes (temp file + rename)
- Proper encoding handling (UTF-8)
- Directory creation with proper permissions

### Agent Integration
- Standardized communication protocols via Markdown files
- Timeout handling for long-running agent tasks
- Agent state management and recovery
- Clear separation of concerns between agents

### Testing Strategy
- Use test-driven development to ensure the functionality is fully described in the tests before implementation.
- Unit tests for each module/function
- Integration tests for agent workflows
- File system state validation
- Mock external dependencies (Ollama)
- Property-based testing for file generation

### Configuration Management
- Environment-based configuration (dev/prod)
- Model selection and parameter tuning
- Agent behavior customization
- Output format preferences

### Code Organization
- Clear module separation by functionality
- Dependency injection for testability
- Interface-based design for swappable components
- Comprehensive docstrings and type hints

## Quality Assurance

Each development step must include:
1. **Unit tests** covering happy path and edge cases
2. **Integration tests** for multi-agent workflows
3. **File validation** ensuring proper structure and format
4. **Error handling** for common failure scenarios
5. **Documentation** with clear examples and usage

## Success Criteria

A successful implementation will:
- Generate complete, audit-ready ISMS documentation in markdown format
- Maintain consistent quality across all generated documents
- Support easy customization and extension
- Provide clear traceability of all decisions and changes
- Enable deployment to GitHub Pages without modification