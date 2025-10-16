#!/bin/bash
# Check for duplicate file processing in inotify logs

LOG_FILE="logs/inotify.log"
LINES=${1:-200}  # Default to last 200 lines, or use first argument

echo "========================================="
echo "  File Deduplication Checker"
echo "========================================="
echo "Checking last $LINES log entries..."
echo ""

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    exit 1
fi

# Extract file paths and count occurrences
DUPLICATES=$(tail -n $LINES "$LOG_FILE" | \
    grep -oP '"file_path": "[^"]+' | \
    sed 's/"file_path": "//' | \
    sort | uniq -c | \
    sort -rn | \
    awk '$1 > 1')

if [ -z "$DUPLICATES" ]; then
    echo "✅ NO DUPLICATES FOUND!"
    echo ""
    echo "All files processed exactly once."
    echo ""
    
    # Show sample of processed files
    echo "Sample of recent files (showing counts):"
    tail -n $LINES "$LOG_FILE" | \
        grep -oP '"file_path": "[^"]+' | \
        sed 's/"file_path": "//' | \
        sort | uniq -c | \
        sort -rn | \
        head -10
else
    echo "❌ DUPLICATES DETECTED!"
    echo ""
    echo "The following files were processed multiple times:"
    echo "$DUPLICATES"
    echo ""
    echo "This indicates the deduplication fix may not be working correctly."
fi

echo ""
echo "========================================="
echo "  Service Status"
echo "========================================="

# Check if service is running
if pgrep -f "python.*app.py" > /dev/null; then
    PID=$(pgrep -f "python.*app.py")
    echo "✅ Service running (PID: $PID)"
    
    # Show tagged_files count from status if available
    if command -v curl &> /dev/null; then
        STATUS=$(curl -s http://localhost:5000/api/monitor/status 2>/dev/null | grep -oP '"tagged_files_count":\s*\K\d+')
        if [ ! -z "$STATUS" ]; then
            echo "📊 Files tracked: $STATUS"
        fi
    fi
else
    echo "⚠️  Service not running"
fi

echo ""

