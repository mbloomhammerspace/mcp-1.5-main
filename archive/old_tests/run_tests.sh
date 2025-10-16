#!/bin/bash

# =============================================================================
# Volume Canvas MCP Server - Comprehensive Test Runner
# =============================================================================
# This script executes all available tests and provides a detailed report
# on any failures encountered during unit testing.
#
# Usage: ./run_tests.sh [options]
# Options:
#   -h, --help          Show this help message
#   -v, --verbose       Enable verbose output
#   -r, --report-only   Only generate report without running tests
#   -c, --coverage      Enable coverage reporting
#   -f, --fail-fast     Stop on first test failure
#   -o, --output FILE   Save report to specific file
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
TESTS_DIR="$PROJECT_ROOT/tests"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
REPORTS_DIR="$PROJECT_ROOT/reports"
LOGS_DIR="$PROJECT_ROOT/logs"

# Default options
VERBOSE=false
REPORT_ONLY=false
COVERAGE=false
FAIL_FAST=false
OUTPUT_FILE=""
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0
TEST_FAILURES=()
TEST_SUITES=()

# Create necessary directories
mkdir -p "$REPORTS_DIR" "$LOGS_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}🧪 Volume Canvas MCP Server - Test Runner${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    echo ""
}

print_help() {
    cat << EOF
Volume Canvas MCP Server - Comprehensive Test Runner

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help          Show this help message and exit
    -v, --verbose       Enable verbose output during test execution
    -r, --report-only   Only generate report without running tests
    -c, --coverage      Enable coverage reporting (requires pytest-cov)
    -f, --fail-fast     Stop on first test failure
    -o, --output FILE   Save detailed report to specific file

EXAMPLES:
    $0                  # Run all tests with default settings
    $0 -v               # Run tests with verbose output
    $0 -c               # Run tests with coverage reporting
    $0 -f               # Stop on first failure
    $0 -o test_report.html  # Save HTML report

TEST TYPES EXECUTED:
    • Unit Tests (pytest)
    • Extended Features Tests
    • Test Harness Integration Tests
    • System Health Checks

EOF
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "$LOGS_DIR/test_runner.log"
    fi
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "$LOGS_DIR/test_runner.log"
}

log_test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    if [[ "$result" == "PASSED" ]]; then
        echo -e "  ✅ ${GREEN}$test_name${NC} - PASSED"
        ((PASSED_TESTS++))
    elif [[ "$result" == "FAILED" ]]; then
        echo -e "  ❌ ${RED}$test_name${NC} - FAILED"
        echo -e "     ${YELLOW}Details:${NC} $details"
        TEST_FAILURES+=("$test_name: $details")
        ((FAILED_TESTS++))
    elif [[ "$result" == "SKIPPED" ]]; then
        echo -e "  ⏭️  ${YELLOW}$test_name${NC} - SKIPPED"
        ((SKIPPED_TESTS++))
    fi
    ((TOTAL_TESTS++))
}

# =============================================================================
# Environment Setup
# =============================================================================

setup_environment() {
    log_info "Setting up test environment..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_error "requirements.txt not found. Please run this script from the project root."
        exit 1
    fi
    
    # Check Python installation
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ -d "$PROJECT_ROOT/.venv" ]]; then
        log_info "Activating virtual environment..."
        source "$PROJECT_ROOT/.venv/bin/activate"
    else
        log_warning "Virtual environment not found. Using system Python."
    fi
    
    # Install/update dependencies if needed
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        log_info "Checking dependencies..."
        pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
    fi
    
    # Ensure pytest and required plugins are installed
    pip install pytest pytest-asyncio pytest-cov pytest-html --quiet
    
    log_success "Environment setup complete"
}

# =============================================================================
# Test Execution Functions
# =============================================================================

run_pytest_tests() {
    log_info "Running pytest unit tests..."
    
    local pytest_args=("-v" "--tb=short")
    local test_files=()
    
    # Add coverage if requested
    if [[ "$COVERAGE" == "true" ]]; then
        pytest_args+=("--cov=src" "--cov-report=html:$REPORTS_DIR/coverage_html" "--cov-report=term-missing")
    fi
    
    # Add fail-fast if requested
    if [[ "$FAIL_FAST" == "true" ]]; then
        pytest_args+=("-x")
    fi
    
    # Find test files
    if [[ -d "$TESTS_DIR" ]]; then
        while IFS= read -r -d '' file; do
            test_files+=("$file")
        done < <(find "$TESTS_DIR" -name "test_*.py" -print0)
    fi
    
    if [[ ${#test_files[@]} -eq 0 ]]; then
        log_warning "No pytest test files found in $TESTS_DIR"
        return 0
    fi
    
    # Run pytest
    local pytest_output
    local pytest_exit_code
    
    if [[ "$VERBOSE" == "true" ]]; then
        pytest_output=$(pytest "${pytest_args[@]}" "${test_files[@]}" 2>&1)
        pytest_exit_code=$?
    else
        pytest_output=$(pytest "${pytest_args[@]}" "${test_files[@]}" 2>&1 | tee "$REPORTS_DIR/pytest_output.log")
        pytest_exit_code=$?
    fi
    
    # Parse pytest results
    local passed=$(echo "$pytest_output" | grep -c "PASSED" || true)
    local failed=$(echo "$pytest_output" | grep -c "FAILED" || true)
    local skipped=$(echo "$pytest_output" | grep -c "SKIPPED" || true)
    
    TEST_SUITES+=("pytest: $passed passed, $failed failed, $skipped skipped")
    
    if [[ $pytest_exit_code -eq 0 ]]; then
        log_success "Pytest tests completed successfully"
    else
        log_error "Pytest tests failed"
        echo "$pytest_output" > "$REPORTS_DIR/pytest_failures.log"
    fi
    
    return $pytest_exit_code
}

run_extended_features_tests() {
    log_info "Running extended features tests..."
    
    if [[ -f "$SCRIPTS_DIR/test_extended_features.py" ]]; then
        local output
        local exit_code
        
        if [[ "$VERBOSE" == "true" ]]; then
            output=$(python3 "$SCRIPTS_DIR/test_extended_features.py" 2>&1)
            exit_code=$?
        else
            output=$(python3 "$SCRIPTS_DIR/test_extended_features.py" 2>&1 | tee "$REPORTS_DIR/extended_features_output.log")
            exit_code=$?
        fi
        
        if [[ $exit_code -eq 0 ]]; then
            log_success "Extended features tests completed successfully"
            TEST_SUITES+=("extended_features: passed")
        else
            log_error "Extended features tests failed"
            echo "$output" > "$REPORTS_DIR/extended_features_failures.log"
            TEST_SUITES+=("extended_features: failed")
        fi
        
        return $exit_code
    else
        log_warning "Extended features test script not found: $SCRIPTS_DIR/test_extended_features.py"
        return 0
    fi
}

run_test_harness() {
    log_info "Running test harness integration tests..."
    
    if [[ -f "$SCRIPTS_DIR/test_harness.py" ]]; then
        local output
        local exit_code
        
        # Run test harness with health checks only to avoid server conflicts
        if [[ "$VERBOSE" == "true" ]]; then
            output=$(python3 "$SCRIPTS_DIR/test_harness.py" --health-only 2>&1)
            exit_code=$?
        else
            output=$(python3 "$SCRIPTS_DIR/test_harness.py" --health-only 2>&1 | tee "$REPORTS_DIR/test_harness_output.log")
            exit_code=$?
        fi
        
        if [[ $exit_code -eq 0 ]]; then
            log_success "Test harness completed successfully"
            TEST_SUITES+=("test_harness: passed")
        else
            log_error "Test harness failed"
            echo "$output" > "$REPORTS_DIR/test_harness_failures.log"
            TEST_SUITES+=("test_harness: failed")
        fi
        
        return $exit_code
    else
        log_warning "Test harness script not found: $SCRIPTS_DIR/test_harness.py"
        return 0
    fi
}

# =============================================================================
# Report Generation
# =============================================================================

generate_text_report() {
    local report_file="${1:-$REPORTS_DIR/test_report_$TIMESTAMP.txt}"
    
    {
        echo "Volume Canvas MCP Server - Test Report"
        echo "======================================"
        echo "Generated: $(date)"
        echo "Project: $PROJECT_ROOT"
        echo ""
        
        echo "Test Summary:"
        echo "  Total Tests: $TOTAL_TESTS"
        echo "  Passed: $PASSED_TESTS"
        echo "  Failed: $FAILED_TESTS"
        echo "  Skipped: $SKIPPED_TESTS"
        echo "  Success Rate: $(( (PASSED_TESTS * 100) / (TOTAL_TESTS > 0 ? TOTAL_TESTS : 1) ))%"
        echo ""
        
        if [[ ${#TEST_SUITES[@]} -gt 0 ]]; then
            echo "Test Suite Results:"
            for suite in "${TEST_SUITES[@]}"; do
                echo "  • $suite"
            done
            echo ""
        fi
        
        if [[ ${#TEST_FAILURES[@]} -gt 0 ]]; then
            echo "Test Failures:"
            for failure in "${TEST_FAILURES[@]}"; do
                echo "  ❌ $failure"
            done
            echo ""
        fi
        
        echo "Detailed Logs:"
        echo "  • Test Runner Log: $LOGS_DIR/test_runner.log"
        echo "  • Pytest Output: $REPORTS_DIR/pytest_output.log"
        echo "  • Extended Features: $REPORTS_DIR/extended_features_output.log"
        echo "  • Test Harness: $REPORTS_DIR/test_harness_output.log"
        
        if [[ "$COVERAGE" == "true" ]]; then
            echo "  • Coverage Report: $REPORTS_DIR/coverage_html/index.html"
        fi
        
    } > "$report_file"
    
    log_info "Text report generated: $report_file"
    echo "$report_file"
}

generate_html_report() {
    local report_file="${1:-$REPORTS_DIR/test_report_$TIMESTAMP.html}"
    
    cat > "$report_file" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Volume Canvas MCP Server - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .summary-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #007bff; }
        .summary-card.failed { border-left-color: #dc3545; }
        .summary-card.passed { border-left-color: #28a745; }
        .summary-card.skipped { border-left-color: #ffc107; }
        .summary-card h3 { margin: 0 0 10px 0; color: #333; }
        .summary-card .number { font-size: 2em; font-weight: bold; }
        .failures { background: #fff5f5; border: 1px solid #fed7d7; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
        .failure-item { background: white; border-left: 4px solid #e53e3e; padding: 10px; margin: 10px 0; border-radius: 4px; }
        .suites { background: #f0f8ff; border: 1px solid #bee3f8; border-radius: 8px; padding: 15px; }
        .suite-item { background: white; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 4px solid #3182ce; }
        .logs { background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; }
        .log-link { color: #3182ce; text-decoration: none; }
        .log-link:hover { text-decoration: underline; }
        .footer { text-align: center; margin-top: 20px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Volume Canvas MCP Server - Test Report</h1>
            <p>Generated: $(date)</p>
            <p>Project: $PROJECT_ROOT</p>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="number">$TOTAL_TESTS</div>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="number">$PASSED_TESTS</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="number">$FAILED_TESTS</div>
            </div>
            <div class="summary-card skipped">
                <h3>Skipped</h3>
                <div class="number">$SKIPPED_TESTS</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <h2>Success Rate: $(( (PASSED_TESTS * 100) / (TOTAL_TESTS > 0 ? TOTAL_TESTS : 1) ))%</h2>
        </div>
EOF

    if [[ ${#TEST_FAILURES[@]} -gt 0 ]]; then
        cat >> "$report_file" << EOF
        <div class="failures">
            <h2>❌ Test Failures</h2>
EOF
        for failure in "${TEST_FAILURES[@]}"; do
            cat >> "$report_file" << EOF
            <div class="failure-item">
                <strong>$failure</strong>
            </div>
EOF
        done
        cat >> "$report_file" << EOF
        </div>
EOF
    fi

    if [[ ${#TEST_SUITES[@]} -gt 0 ]]; then
        cat >> "$report_file" << EOF
        <div class="suites">
            <h2>📊 Test Suite Results</h2>
EOF
        for suite in "${TEST_SUITES[@]}"; do
            cat >> "$report_file" << EOF
            <div class="suite-item">• $suite</div>
EOF
        done
        cat >> "$report_file" << EOF
        </div>
EOF
    fi

    cat >> "$report_file" << EOF
        <div class="logs">
            <h2>📋 Detailed Logs</h2>
            <p><a href="file://$LOGS_DIR/test_runner.log" class="log-link">Test Runner Log</a></p>
            <p><a href="file://$REPORTS_DIR/pytest_output.log" class="log-link">Pytest Output</a></p>
            <p><a href="file://$REPORTS_DIR/extended_features_output.log" class="log-link">Extended Features Log</a></p>
            <p><a href="file://$REPORTS_DIR/test_harness_output.log" class="log-link">Test Harness Log</a></p>
EOF

    if [[ "$COVERAGE" == "true" ]]; then
        cat >> "$report_file" << EOF
            <p><a href="file://$REPORTS_DIR/coverage_html/index.html" class="log-link">Coverage Report</a></p>
EOF
    fi

    cat >> "$report_file" << EOF
        </div>
        
        <div class="footer">
            <p>Report generated by Volume Canvas MCP Server Test Runner</p>
        </div>
    </div>
</body>
</html>
EOF
    
    log_info "HTML report generated: $report_file"
    echo "$report_file"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                print_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -r|--report-only)
                REPORT_ONLY=true
                shift
                ;;
            -c|--coverage)
                COVERAGE=true
                shift
                ;;
            -f|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            *)
                log_error "Unknown option: $1"
                print_help
                exit 1
                ;;
        esac
    done
    
    print_header
    
    if [[ "$REPORT_ONLY" == "true" ]]; then
        log_info "Report-only mode - generating reports from existing data"
        if [[ -n "$OUTPUT_FILE" ]]; then
            generate_text_report "$OUTPUT_FILE"
            generate_html_report "${OUTPUT_FILE%.*}.html"
        else
            generate_text_report
            generate_html_report
        fi
        exit 0
    fi
    
    # Setup environment
    setup_environment
    
    # Initialize counters
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    SKIPPED_TESTS=0
    TEST_FAILURES=()
    TEST_SUITES=()
    
    local overall_exit_code=0
    
    # Run all test suites
    log_info "Starting comprehensive test execution..."
    
    # 1. Run pytest unit tests
    if ! run_pytest_tests; then
        overall_exit_code=1
    fi
    
    # 2. Run extended features tests
    if ! run_extended_features_tests; then
        overall_exit_code=1
    fi
    
    # 3. Run test harness
    if ! run_test_harness; then
        overall_exit_code=1
    fi
    
    # Generate reports
    log_info "Generating test reports..."
    
    local text_report
    local html_report
    
    if [[ -n "$OUTPUT_FILE" ]]; then
        text_report=$(generate_text_report "$OUTPUT_FILE")
        html_report=$(generate_html_report "${OUTPUT_FILE%.*}.html")
    else
        text_report=$(generate_text_report)
        html_report=$(generate_html_report)
    fi
    
    # Print summary
    echo ""
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "${BLUE}📊 Test Execution Summary${NC}"
    echo -e "${BLUE}==============================================================================${NC}"
    echo -e "Total Tests: ${CYAN}$TOTAL_TESTS${NC}"
    echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
    echo -e "Skipped: ${YELLOW}$SKIPPED_TESTS${NC}"
    echo -e "Success Rate: ${CYAN}$(( (PASSED_TESTS * 100) / (TOTAL_TESTS > 0 ? TOTAL_TESTS : 1) ))%${NC}"
    echo ""
    
    if [[ ${#TEST_FAILURES[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Test Failures:${NC}"
        for failure in "${TEST_FAILURES[@]}"; do
            echo -e "  • ${RED}$failure${NC}"
        done
        echo ""
    fi
    
    echo -e "📋 Reports generated:"
    echo -e "  • Text Report: ${CYAN}$text_report${NC}"
    echo -e "  • HTML Report: ${CYAN}$html_report${NC}"
    
    if [[ "$COVERAGE" == "true" ]]; then
        echo -e "  • Coverage Report: ${CYAN}$REPORTS_DIR/coverage_html/index.html${NC}"
    fi
    
    echo ""
    
    if [[ $overall_exit_code -eq 0 ]]; then
        log_success "All tests completed successfully! 🎉"
    else
        log_error "Some tests failed. Check the reports for details."
    fi
    
    exit $overall_exit_code
}

# Run main function with all arguments
main "$@"
