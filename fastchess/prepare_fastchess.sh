#!/bin/bash

set -e

# Clone the Fastchess repository
echo "Cloning Fastchess repository..."
git clone https://github.com/AndyGrant/Fastchess

# Build Fastchess
echo "Building Fastchess..."
cd Fastchess
make -j build=release

# Move the executable to artifacts directory
echo "Moving fastchess executable to artifacts..."
mv fastchess ../artifacts/

# Clean up the cloned repository
echo "Cleaning up..."
cd ..
rm -rf Fastchess

echo "Done! fastchess executable is in artifacts/"
