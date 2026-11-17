FROM python:3.11-slim

# 1. Install HTTPS certificates, curl, and build tools
RUN apt-get update && apt-get install -y \
    ca-certificates \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Download precompiled ttyd binary for the container's architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then BIN_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then BIN_ARCH="aarch64"; \
    else echo "Unsupported arch: $ARCH" && exit 1; fi && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.${BIN_ARCH}" -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

# 3. Pre-install Rust so install_and_run.sh doesn't pause for prompts
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup.sh && \
    sh /tmp/rustup.sh -y --no-modify-path && \
    rm -f /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# 4. Copy all untouched repository files into the container
COPY . /app
WORKDIR /app

# 5. Make the repository's Linux script executable
RUN chmod +x install_and_run.sh

# 6. Expose Render's default port and launch ttyd interactively
EXPOSE 10000
CMD ["ttyd", "-p", "10000", "-W", "bash", "-c", "./install_and_run.sh; exec bash"]
