# Contributing to MARA

Thanks for your interest in contributing to MARA. This document covers the process for submitting changes.

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/mara.git
cd mara
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -e ".[dev]"
```

## Code Standards

MARA uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting, and [mypy](https://mypy-lang.org/) for type checking.

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy mara/
```

## Running Tests

```bash
pytest
pytest --cov=mara  # with coverage
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests pass and linting is clean.
4. Update documentation if you're changing public APIs.
5. Submit a PR with a clear description of what changed and why.

## Building Custom Agents

The most common contribution is new agents. See the [agent documentation](README.md#custom-agents) for the base class interface. Every new agent should include:

- Clear docstring explaining what the agent does and when to use it
- Sensible `AgentConfig` defaults
- At least one test covering the `execute` method
- An entry in the agents table in the README if it's a general-purpose agent

## Reporting Issues

Open an issue with:
- What you expected to happen
- What actually happened
- Steps to reproduce
- MARA version and Python version

## Code of Conduct

Be respectful. Build things that help people. That's it.
