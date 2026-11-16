FROM python:3.11-slim

# 1. Install curl, build tools, and ttyd (turns the terminal into a website/app)
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    ttyd \
    && rm -rf /var/lib/apt/lists/*

# 2. Pre-install Rust so install_and_run.sh doesn't pause for prompts
RUN curl --proto '=https' --tlsv1.2 -sSf https://rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# 3. Copy all untouched repository files into the container
COPY . /app
WORKDIR /app

# 4. Make the repository's Linux script executable
RUN chmod +x install_and_run.sh

# 5. Stream the Linux script directly to your Render website URL on port 10000
EXPOSE 10000
CMD ["ttyd", "-p", "10000", "-W", "-c", "admin:Balogun90", "./install_and_run.sh"]
