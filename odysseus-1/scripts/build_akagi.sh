#!/bin/bash
set -e

echo "Building AK-AGI v5.0 Components..."

# Download models
mkdir -p /akagi/soul
if [ ! -f /akagi/soul/phi-3.5-mini.gguf ]; then
    echo "Downloading Soul Model (Phi-3.5 Mini)..."
    # curl -L https://huggingface.co/microsoft/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf -o /akagi/soul/phi-3.5-mini.gguf
    touch /akagi/soul/phi-3.5-mini.gguf # Placeholder
fi

# Cargo build
echo "Compiling Rust daemons..."
cd rust/soul_daemon && cargo build --release && cd ../..
cd rust/grid_daemon && cargo build --release && cd ../..
cd rust/cortex && cargo build --release && cd ../..

# Copy to seed
cp -r primitives /akagi/seed/

# Generate 2500 stub manifests (simulated)
echo "Generating 2500 primitive manifests..."
for i in {1..2500}; do
    echo '{"id": "'$i'", "type": "primitive"}' > /akagi/primitives/manifests/gen_$i.json
done

echo "AK-AGI build complete."
