FROM python:3.11-slim

# -----------------------------
# SYSTEM DEPENDENCIES
# -----------------------------
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    zstd \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# INSTALL OLLAMA
# -----------------------------
RUN curl -fsSL https://ollama.com/install.sh | sh

# -----------------------------
# WORK DIRECTORY
# -----------------------------
WORKDIR /app

# -----------------------------
# COPY PROJECT
# -----------------------------
COPY . .

# -----------------------------
# PYTHON DEPENDENCIES
# -----------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------
# CREATE PERSISTENT DIRECTORIES
# -----------------------------
RUN mkdir -p /app/data /app/logs

# -----------------------------
# EXPOSE OLLAMA PORT
# -----------------------------
EXPOSE 11434

# -----------------------------
# START SYSTEM
# -----------------------------
CMD bash -c "\
ollama serve & \
sleep 10 && \
ollama pull llama3.1:8b && \
ollama pull nomic-embed-text && \
python main.py"