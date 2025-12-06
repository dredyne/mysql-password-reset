#!/bin/bash
# MySQL Password Reset Tool - Linux/Mac Shell Script
# This script runs the MySQL password reset tool with sudo privileges

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.6 or higher:"
    echo "  Ubuntu/Debian: sudo apt-get install python3"
    echo "  CentOS/RHEL:   sudo yum install python3"
    echo "  macOS:         brew install python3"
    exit 1
fi

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "ERROR: This script requires root privileges"
    echo "Please run with sudo: sudo $0"
    exit 1
fi

# Run the MySQL reset script
echo "Running MySQL Password Reset Tool..."
echo ""
python3 "$SCRIPT_DIR/src/main.py"

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "SUCCESS: Password reset completed"
else
    echo ""
    echo "FAILED: Password reset did not complete successfully"
fi

exit $EXIT_CODE
