#!/bin/bash
set -e

echo "AK-AGI v5.0 Iron God Protocol Bootstrapping..."

# Check AVX2
if grep -q avx2 /proc/cpuinfo; then
    echo "AVX2 detected. High-performance mode enabled."
else
    echo "AVX2 NOT detected. Falling back to compatibility mode."
fi

# Create staging dirs
mkdir -p /akagi/{soul,vault,primitives,run,logs,seed,overlay,work,active}

# ZRAM configuration (requires root/sudo, usually handled by sys-admin but requested here)
# echo "Configuring zram lz4hc 6G..."
# modprobe zram
# echo lz4hc > /sys/block/zram0/comp_algorithm
# echo 6G > /sys/block/zram0/disksize
# mkswap /dev/zram0
# swapon /dev/zram0 -p 100
# sysctl vm.swappiness=10

# Launch Daemons (Background)
echo "Launching Soul Daemon..."
./rust/soul_daemon/target/release/soul_daemon &

echo "Launching Grid Daemon..."
./rust/grid_daemon/target/release/grid_daemon &

echo "Launching Cortex..."
./rust/cortex/target/release/cortex &

# Launch FastAPI
echo "Launching FastAPI (Uvicorn)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
