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

# 3. Pre-install Rust so native packages build cleanly without prompts
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rustup.sh && \
    sh /tmp/rustup.sh -y --no-modify-path && \
    rm -f /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# 4. Copy all untouched repository files into /app
COPY . /app
WORKDIR /app

# 5. Install solana so sol_utils.py finds it automatically
RUN pip install --no-cache-dir solana

# 6. Make the repository's Linux script executable
RUN chmod +x install_and_run.sh

# 7. Expose Render's default port and launch ttyd interactively
EXPOSE 10000
CMD ["ttyd", "-p", "10000", "-W", \
     "-t", "fontSize=15", \
     "-t", "lineHeight=1.25", \
     "-t", "cursorStyle=bar", \
     "-t", "theme={\"background\":\"#0f172a\",\"foreground\":\"#e2e8f0\"}", \
     "bash", "-c", "./install_and_run.sh; exec bash"]

