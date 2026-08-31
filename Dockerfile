FROM osrf/ros:jazzy-desktop-full

ARG USERNAME=rosdev
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive

# Development tooling on top of the desktop-full base.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash-completion \
        build-essential \
        cmake \
        gdb \
        git \
        iproute2 \
        iputils-ping \
        less \
        mesa-utils \
        nano \
        python3-colcon-common-extensions \
        python3-colcon-mixin \
        python3-pip \
        python3-vcstool \
        ros-dev-tools \
        ros-jazzy-rmw-cyclonedds-cpp \
        sudo \
        tmux \
        udev \
        usbutils \
        vim \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Simulation: TurtleBot3 on Gazebo Harmonic, exposing the same /cmd_vel, /odom
# and /scan interface a real mobile base does. Pulls in ros_gz as a dependency.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-jazzy-teleop-twist-keyboard \
        ros-jazzy-turtlebot3-gazebo \
        ros-jazzy-turtlebot3-teleop \
    && rm -rf /var/lib/apt/lists/*

ENV TURTLEBOT3_MODEL=burger

# Ubuntu 24.04 images ship a default "ubuntu" account at UID 1000. Reuse that
# slot so files created in the mounted workspace are owned by the host user.
RUN if getent passwd ${UID} >/dev/null; then \
        old=$(getent passwd ${UID} | cut -d: -f1); \
        [ "$old" = "${USERNAME}" ] || usermod -l ${USERNAME} -d /home/${USERNAME} -m "$old"; \
        groupmod -n ${USERNAME} "$(getent group ${GID} | cut -d: -f1)" || true; \
    else \
        groupadd -g ${GID} ${USERNAME} && \
        useradd -m -u ${UID} -g ${GID} -s /bin/bash ${USERNAME}; \
    fi && \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} && \
    chmod 0440 /etc/sudoers.d/${USERNAME} && \
    usermod -aG dialout,video,plugdev ${USERNAME}

# snap-confined Docker cannot bind-mount /usr/lib/wsl, so the three libraries
# Mesa's d3d12 driver needs for GPU-accelerated GL are baked in instead.
# run.sh refreshes ./.wslgpu from the host before building.
COPY .wslgpu/ /usr/lib/wsl/lib/
ENV LD_LIBRARY_PATH=/usr/lib/wsl/lib

# Source the ROS underlay plus the workspace overlay. This lives in profile.d
# rather than only in .bashrc because .bashrc returns early for non-interactive
# shells, which would break `docker compose exec ros bash -lc '...'`.
RUN printf '%s\n' \
        'source /opt/ros/jazzy/setup.bash' \
        '[ -f /ws/install/setup.bash ] && source /ws/install/setup.bash' \
        > /etc/profile.d/10-ros.sh && \
    chmod 0644 /etc/profile.d/10-ros.sh

# Qt refuses a world-writable XDG_RUNTIME_DIR, and /mnt/wslg/runtime-dir is 0777.
# Use a private dir that links back to the WSLg sockets instead.
RUN mkdir -p -m 0700 /run/user/${UID} && \
    ln -s /mnt/wslg/runtime-dir/wayland-0 /run/user/${UID}/wayland-0 && \
    ln -s /mnt/wslg/runtime-dir/pulse /run/user/${UID}/pulse && \
    chown -R ${UID}:${GID} /run/user/${UID}

USER ${USERNAME}
WORKDIR /ws

# Create the cache dir before the named volume is mounted over it, so the volume
# inherits this ownership instead of being created root-owned (Mesa shader cache).
RUN mkdir -p /home/${USERNAME}/.cache

# Interactive shells skip profile.d, so wire the same setup into .bashrc.
RUN printf '%s\n' \
        'source /etc/profile.d/10-ros.sh' \
        'source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash' \
        >> /home/${USERNAME}/.bashrc

CMD ["bash"]
