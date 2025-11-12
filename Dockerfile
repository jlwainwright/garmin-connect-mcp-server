FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server script and modules
COPY garmin_mcp_server_fixed.py .
COPY modules/ ./modules/

# Set environment variables with defaults
ENV GARMIN_EMAIL=""
ENV GARMIN_PASSWORD=""
ENV GARMIN_MFA_CODE=""
ENV NTFY_SERVER=""
ENV NTFY_TOPIC=""
ENV NTFY_TOKEN=""
ENV HOME="/root"
ENV USER="garmin"

# Expose the server (MCP uses stdio, so this is informational)
LABEL org.opencontainers.image.title="Garmin Connect MCP Server"
LABEL org.opencontainers.image.description="MCP server for Garmin Connect data"
LABEL org.opencontainers.image.version="1.0.0"

# Run the server
CMD ["python", "garmin_mcp_server_fixed.py"]
