# Project Guidelines

## Python Style
- Prefer custom classes and data structures over dictionaries
- Use `pathlib` instead of `os.path`
- Import modules, not classes (`import module` then `module.Class`, not `from module import Class`)
- Keep methods minimal; factor out logical sections into sub-methods
- Avoid importing inside methods
- Keep classes small, preferably under 400 lines

## Testing
- Use `unittest`
- One `TestCase` class per module
- No docstrings on test methods
- No `main()` or `unittest.main()` in test modules
- Run tests after each significant change: `python -m unittest`
- Maintain >80% code coverage for math and core modules
- Use `setUp()` and `tearDown()` for test fixtures

## Documentation
- Docstrings for complex logic only
- Use single-line docstrings where appropriate
- Avoid verbose docstrings on simple methods
- Avoid docstrings on test methods

