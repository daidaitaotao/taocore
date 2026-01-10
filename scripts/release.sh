#!/bin/bash
# TaoCore Release Script
# This script guides you through the release process

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}TaoCore Release Script${NC}"
echo "================================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found. Run this from the project root.${NC}"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo -e "Current version: ${YELLOW}$CURRENT_VERSION${NC}"
echo ""

# Ask for new version
read -p "Enter new version number (e.g., 0.1.1): " NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo -e "${RED}Error: Version number cannot be empty${NC}"
    exit 1
fi

echo ""
echo "Release plan:"
echo "  Current: $CURRENT_VERSION"
echo "  New:     $NEW_VERSION"
echo ""

# Confirm
read -p "Continue with release? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${GREEN}Step 1: Running tests...${NC}"
make test || { echo -e "${RED}Tests failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}Step 2: Running tox...${NC}"
make tox || { echo -e "${RED}Tox tests failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}Step 3: Running linter...${NC}"
make lint || { echo -e "${RED}Linting failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}Step 4: Updating version...${NC}"
sed -i.bak "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

echo ""
echo -e "${YELLOW}Action required: Update CHANGELOG.md${NC}"
echo "Press Enter when done..."
read

echo ""
echo -e "${GREEN}Step 5: Cleaning old builds...${NC}"
make clean
rm -rf dist/

echo ""
echo -e "${GREEN}Step 6: Building package...${NC}"
make build || { echo -e "${RED}Build failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}Step 7: Checking distributions...${NC}"
make check-dist || { echo -e "${RED}Distribution check failed!${NC}"; exit 1; }

echo ""
echo -e "${GREEN}Step 8: Git operations...${NC}"
git add pyproject.toml CHANGELOG.md
git commit -m "Release v$NEW_VERSION"
git tag -a "v$NEW_VERSION" -m "Version $NEW_VERSION"

echo ""
echo -e "${YELLOW}Choose publishing option:${NC}"
echo "  1) Publish to TestPyPI (recommended)"
echo "  2) Publish to PyPI (production)"
echo "  3) Skip publishing (just prepare)"
read -p "Enter choice [1-3]: " -n 1 -r PUBLISH_CHOICE
echo

case $PUBLISH_CHOICE in
    1)
        echo ""
        echo -e "${GREEN}Publishing to TestPyPI...${NC}"
        make publish-test
        echo ""
        echo -e "${GREEN}Test installation:${NC}"
        echo "  pip install --index-url https://test.pypi.org/simple/ taocore==$NEW_VERSION"
        ;;
    2)
        echo ""
        echo -e "${RED}Publishing to PyPI (PRODUCTION)...${NC}"
        make publish
        ;;
    3)
        echo ""
        echo -e "${YELLOW}Skipping publish.${NC}"
        ;;
    *)
        echo ""
        echo -e "${YELLOW}Invalid choice. Skipping publish.${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}Step 9: Push to GitHub${NC}"
read -p "Push to GitHub? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin main
    git push origin "v$NEW_VERSION"
    echo -e "${GREEN}Pushed to GitHub!${NC}"
else
    echo -e "${YELLOW}Remember to push manually:${NC}"
    echo "  git push origin main"
    echo "  git push origin v$NEW_VERSION"
fi

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Release v$NEW_VERSION complete!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Create GitHub release at https://github.com/yourusername/taocore/releases"
echo "  2. Verify package on PyPI: https://pypi.org/project/taocore/"
echo "  3. Test installation: pip install taocore==$NEW_VERSION"
