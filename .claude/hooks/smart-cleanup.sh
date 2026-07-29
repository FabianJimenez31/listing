#!/bin/bash
# Smart cleanup script to clean temporary log files, backups, and scrap files.

set -e

PROJECT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_DIR"

echo "🧹 Running Smart Cleanup..."

# Remove python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.py[co]" -delete 2>/dev/null || true

# Remove temporary logs or test outputs in root directory
find . -maxdepth 1 -type f -name "*.log" -delete 2>/dev/null || true
find . -maxdepth 1 -type f -name "critical_tests.log" -delete 2>/dev/null || true

# Remove swap files or editor backups
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true

echo "✅ Smart Cleanup completed successfully!"
exit 0
