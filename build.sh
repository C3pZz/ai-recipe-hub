#!/bin/bash
# AI Recipe Hub - Build Script
# Usage: ./build.sh [--serve]

set -e

echo "🔨 Building AI Recipe Hub..."

# Hugo build
hugo --minify

# Pagefind indexing
echo "🔍 Building Pagefind search index..."
pagefind --site public --output-path public/pagefind

echo "✅ Build complete! Output: ./public/"

# Serve if requested
if [ "$1" = "--serve" ]; then
  echo "🌐 Starting local server at http://localhost:8080"
  cd public && python3 -m http.server 8080
fi
