#!/bin/bash
set -e

BASE_BRANCH="master"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
WORKING_DIR=$(pwd)

if [ -n "$1" ]; then
    RELEASE_DIR="$1"
else
    RELEASE_DIR="$WORKING_DIR/pr_releases_changelog"
fi

# Ensure you're not on master
if [ "$CURRENT_BRANCH" == "$BASE_BRANCH" ]; then
    echo "You're already on $BASE_BRANCH. Nothing to close."
    exit 1
fi

# Fetch latest master branch
git fetch origin $BASE_BRANCH

# Count commits ahead of master
COMMIT_COUNT=$(git rev-list --count origin/$BASE_BRANCH..HEAD)
echo "This branch is $COMMIT_COUNT commits ahead of $BASE_BRANCH."

# Sanitize the branch name for file naming
SAFE_BRANCH_NAME=$(echo "$CURRENT_BRANCH" | tr '/: *' '____')

# Ensure the output directory exists
mkdir -p "$RELEASE_DIR"

# Full path to changelog file
OUTPUT_FILE="$RELEASE_DIR/changelog_${SAFE_BRANCH_NAME}.md"

# Run your changelog generator
echo "Generating AI changelog for $COMMIT_COUNT commits..."
generate-changelog \
    -n "$COMMIT_COUNT" \
    --batch-output-override "$OUTPUT_FILE"

# Stage, commit, and push the changelog
git add "$OUTPUT_FILE"
git commit -m "Add changelog for $CURRENT_BRANCH before PR"
git push origin "$CURRENT_BRANCH"

# OPTIONAL: Open PR with GitHub CLI
if command -v gh &> /dev/null; then
    echo "Creating pull request via GitHub CLI..."
    gh pr create --base "$BASE_BRANCH" --head "$CURRENT_BRANCH" --fill
else
    echo "GitHub CLI not installed. Skipping PR creation."
fi
