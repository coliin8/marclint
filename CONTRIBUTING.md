# Contributing to marc-lint

First off, thank you for considering contributing to marc-lint! 

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Describe the bug and include steps to reproduce
- Include Python version and OS information
- Provide sample MARC records if possible (anonymized if needed)

### Suggesting Enhancements

- Use the GitHub issue tracker with "enhancement" label
- Explain why this enhancement would be useful
- Provide examples of how it would work

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `uv run pytest`
6. Format code: `uv run tox -e format`
7. Run linting: `uv run tox -e lint`
8. Commit your changes (`git commit -m 'Add amazing feature'`)
9. Push to the branch (`git push origin feature/amazing-feature`)
10. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/coliin8/marclint.git
cd marclint

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run tests across Python versions
uv run tox
```

### Coding Standards

- Follow PEP 8 style guide
- Use type hints
- Write docstrings for public APIs
- Add tests for new features
- Keep test coverage high

### Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Test against Python 3.10-3.14 if possible

### Documentation

- Update README.md if adding user-facing features
- Update CHANGELOG.md following Keep a Changelog format
- Add docstrings to new functions/classes
- Update type hints

## Code of Conduct

Be respectful, inclusive, and considerate in all interactions.

## Questions?

Feel free to open an issue for questions or discussion.

Thank you for your contributions! 🎉
