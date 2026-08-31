#!/usr/bin/env bash
# Bring up the TurtleBot3 simulation demo and drive the robot around.
#
#   ./demo.sh            headless sim + RViz2, then autonomous wandering
#   ./demo.sh --gui      same but with the Gazebo window as well (~15% slower)
#   ./demo.sh --stop     shut the demo down
#
# TURTLEBOT3_MODEL=waffle ./demo.sh   picks the camera-equipped model.
#
# Everything runs inside the ros2-jazzy container; run.sh builds it if needed.
set -euo pipefail

cd "$(dirname "$0")"

SERVICE=ros
GUI=0
WANDER_SECONDS=120
# turtlebot3_gazebo's own launch files read this from the environment and abort
# when it is unset, so never rely on the image having defined it.
MODEL="${TURTLEBOT3_MODEL:-burger}"

for arg in "$@"; do
    case "$arg" in
        --gui) GUI=1 ;;
        --stop)
            # Every pattern is bracketed. pkill -f matches against full command
            # lines, which includes the shell running this very command, so an
            # unbracketed pattern would make the shell kill itself before it got
            # to the rest of the list.
            docker compose exec -T "$SERVICE" bash -lc \
                'pkill -f "[t]b3_headless.launch"; pkill -f "[t]urtlebot3_world.launch"; \
                 pkill -f "[g]z sim"; pkill -f "[p]arameter_bridge"; \
                 pkill -f "[r]obot_state_publisher"; pkill -f "[r]viz2 -d"; true'
            echo "demo stopped"
            exit 0
            ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

in_container() { docker compose exec -T "$SERVICE" bash -lc "$1"; }
# setsid detaches the process, otherwise it dies with the exec session. Because
# setsid execs a real program, the command must start with one -- use `env VAR=x`
# to pass variables, never the `export` builtin.
start_detached() { docker compose exec -d "$SERVICE" bash -lc "exec setsid $1"; }

if [ "$(docker inspect -f '{{.State.Running}}' ros2-jazzy 2>/dev/null)" != "true" ]; then
    echo "==> Starting container..."
    docker compose up -d "$SERVICE"
    sleep 5
fi

# Clear the logs first: a stale one from a previous run makes a launch that
# never started look like a launch that failed.
in_container ': > /tmp/demo_gz.log; : > /tmp/demo_rviz.log'

echo "==> Starting Gazebo (this takes ~45s)..."
if [ "$GUI" = "1" ]; then
    start_detached "env TURTLEBOT3_MODEL=$MODEL \
                    ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py \
                    > /tmp/demo_gz.log 2>&1"
else
    start_detached "ros2 launch /ws/launch/tb3_headless.launch.py model:=$MODEL \
                    > /tmp/demo_gz.log 2>&1"
fi

echo -n "    waiting for the robot to come up"
for _ in $(seq 30); do
    if in_container 'ros2 topic list 2>/dev/null | grep -qx /scan'; then
        echo " ok"
        break
    fi
    echo -n "."
    sleep 3
done

if ! in_container 'ros2 topic list 2>/dev/null | grep -qx /scan'; then
    echo
    echo "!! /scan never appeared. Log:" >&2
    in_container 'tail -20 /tmp/demo_gz.log' >&2
    exit 1
fi

echo "==> Starting RViz2..."
start_detached "rviz2 -d /opt/ros/jazzy/share/turtlebot3_gazebo/rviz/tb3_gazebo.rviz > /tmp/demo_rviz.log 2>&1"
sleep 15

echo "==> Robot state:"
in_container 'python3 /ws/scripts/robot.py status'

echo "==> Wandering for ${WANDER_SECONDS}s (Ctrl-C to stop early)..."
in_container "python3 /ws/scripts/robot.py wander $WANDER_SECONDS"

echo
echo "Demo finished. The simulation is still running — drive it yourself with:"
echo "    ./run.sh"
echo "    python3 /ws/scripts/robot.py forward 1.0"
echo "Shut it down with: ./demo.sh --stop"
