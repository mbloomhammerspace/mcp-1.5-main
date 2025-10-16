# 🧪 Test Runner Documentation

## Overview

The `run_tests.sh` script provides comprehensive testing for the Volume Canvas MCP Server project. It executes all available test suites and generates detailed reports on test results and any failures.

## Features

- **Comprehensive Testing**: Runs all test types including unit tests, extended features, and integration tests
- **Detailed Reporting**: Generates both text and HTML reports with failure details
- **Coverage Support**: Optional code coverage reporting
- **Flexible Options**: Multiple execution modes and output formats
- **Failure Tracking**: Detailed tracking and reporting of test failures
- **Environment Setup**: Automatic dependency checking and virtual environment activation

## Usage

### Basic Usage

```bash
# Run all tests with default settings
./run_tests.sh

# Run tests with verbose output
./run_tests.sh -v

# Run tests with coverage reporting
./run_tests.sh -c

# Stop on first test failure
./run_tests.sh -f
```

### Advanced Usage

```bash
# Generate HTML report with custom filename
./run_tests.sh -o my_test_report.html

# Run with all options enabled
./run_tests.sh -v -c -f -o comprehensive_report.html

# Generate report from existing test data
./run_tests.sh --report-only -o existing_report.txt
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit |
| `-v, --verbose` | Enable verbose output during test execution |
| `-r, --report-only` | Only generate report without running tests |
| `-c, --coverage` | Enable coverage reporting (requires pytest-cov) |
| `-f, --fail-fast` | Stop on first test failure |
| `-o, --output FILE` | Save detailed report to specific file |

## Test Types Executed

### 1. Unit Tests (pytest)
- **Location**: `tests/` directory
- **Framework**: pytest with pytest-asyncio
- **Files**: 
  - `test_extended_features.py` - Tests for tagging and objectives functionality
  - `test_volume_canvas_mcp_server.py` - Core MCP server tests

### 2. Extended Features Tests
- **Location**: `scripts/test_extended_features.py`
- **Purpose**: Tests advanced features like tag search and objectives management
- **Type**: Integration tests with mock data

### 3. Test Harness Integration Tests
- **Location**: `scripts/test_harness.py`
- **Purpose**: Comprehensive system health checks and integration testing
- **Type**: End-to-end testing with server startup/shutdown

## Report Formats

### Text Report
- **Location**: `reports/test_report_YYYYMMDD_HHMMSS.txt`
- **Content**: 
  - Test summary statistics
  - Failure details
  - Log file locations
  - Success rate

### HTML Report
- **Location**: `reports/test_report_YYYYMMDD_HHMMSS.html`
- **Content**:
  - Visual test results dashboard
  - Interactive failure details
  - Links to detailed logs
  - Coverage reports (if enabled)

### Coverage Report (Optional)
- **Location**: `reports/coverage_html/index.html`
- **Requirements**: Run with `-c` or `--coverage` option
- **Content**: Code coverage analysis with line-by-line details

## Output Structure

```
reports/
├── test_report_YYYYMMDD_HHMMSS.txt     # Text report
├── test_report_YYYYMMDD_HHMMSS.html    # HTML report
├── pytest_output.log                   # Pytest execution log
├── extended_features_output.log        # Extended features test log
├── test_harness_output.log             # Test harness execution log
└── coverage_html/                      # Coverage reports (if enabled)
    └── index.html

logs/
└── test_runner.log                     # Main test runner log
```

## Environment Requirements

### Dependencies
- Python 3.8+
- pytest and pytest-asyncio
- pytest-cov (for coverage reporting)
- All dependencies from `requirements.txt`

### Virtual Environment
The script automatically detects and activates a virtual environment if present:
- Looks for `.venv/` directory in project root
- Falls back to system Python if no virtual environment found

### Directory Structure
The script expects the following structure:
```
project_root/
├── run_tests.sh           # This script
├── requirements.txt       # Python dependencies
├── tests/                 # Unit tests
├── scripts/               # Test scripts
├── reports/               # Generated reports
└── logs/                  # Execution logs
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   chmod +x run_tests.sh
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio pytest-cov
   ```

3. **Virtual Environment Issues**
   - Ensure `.venv/bin/activate` exists
   - Or run without virtual environment (uses system Python)

4. **Test Failures**
   - Check detailed logs in `reports/` directory
   - Review HTML report for visual failure details
   - Use `-v` flag for verbose output during execution

### Debug Mode

For debugging test issues:
```bash
# Run with maximum verbosity
./run_tests.sh -v -f

# Check individual test logs
cat reports/pytest_output.log
cat reports/extended_features_output.log
cat reports/test_harness_output.log
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Tests
  run: |
    chmod +x run_tests.sh
    ./run_tests.sh -c -o test_results.html
    
- name: Upload Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: reports/
```

### Exit Codes
- `0`: All tests passed
- `1`: One or more tests failed
- Use exit codes for CI/CD pipeline integration

## Contributing

When adding new tests:

1. **Unit Tests**: Add to `tests/` directory with `test_` prefix
2. **Integration Tests**: Add to `scripts/` directory
3. **Update Documentation**: Update this README if new test types are added

## Support

For issues with the test runner:
1. Check this documentation
2. Review generated logs in `reports/` and `logs/` directories
3. Run with `-v` flag for detailed output
4. Ensure all dependencies are installed correctly
