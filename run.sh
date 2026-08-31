#!/usr/bin/env bash
# Open a shell in the ROS 2 Jazzy container, starting or building it if needed.
# Run it again from another terminal to attach a second shell to the same container.
set -euo pipefail

cd "$(dirname "$0")"

SERVICE=ros
CONTAINER=ros2-jazzy

# Mesa's d3d12 driver needs these host libraries to reach the GPU. snap-confined
# Docker cannot bind-mount /usr/lib/wsl, so they are staged into the build context.
if [ -d /usr/lib/wsl/lib ]; then
    mkdir -p .wslgpu
    for lib in libd3d12.so libd3d12core.so libdxcore.so; do
        cp -u "/usr/lib/wsl/lib/$lib" .wslgpu/ 2>/dev/null || true
    done
fi

if ! docker image inspect ros2-jazzy-dev >/dev/null 2>&1; then
    echo "==> Image not found, building (first run takes a few minutes)..."
    docker compose build "$SERVICE"
fi

if [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null)" != "true" ]; then
    echo "==> Starting $CONTAINER..."
    docker compose up -d "$SERVICE"
fi

exec docker compose exec "$SERVICE" bash
