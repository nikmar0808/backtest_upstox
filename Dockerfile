# --- Stage 1: Build Layer for Heavy Python Libraries ---
FROM python:3.14-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install tools needed to compile math & chart libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compile all libraries into wheel binaries in a single clean pass
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# --- Stage 2: Clean Secure Runtime ---
FROM python:3.14-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create a secure user named backtestuser so your code doesn't run as "root"
RUN useradd -u 8888 backtestuser && chown -R backtestuser:backtestuser /app

# Bring over and install the compiled libraries
COPY --from=builder /build/wheels /tmp/wheels
COPY --from=builder /build/requirements.txt .
RUN pip install --no-cache /tmp/wheels/* && rm -rf /tmp/wheels

# Copy your code into the container assigning proper user rights
COPY --chown=backtestuser:backtestuser backtest_common/ ./backtest_common/
COPY --chown=backtestuser:backtestuser upstox_core/ ./upstox_core/

# FIX: Pull the files from the test_client subfolder instead of the root folder
COPY --chown=backtestuser:backtestuser test_client/PnL_Optimizer_cls.py test_client/UpstoxBackTestManager_cls.py ./

# --- FIXED LOGIC LOCATION ---
# Create folders where your backtest reports and logs will live while still ROOT
RUN mkdir -p datafiles/RawData datafiles/Reports datafiles/Signals datafiles/TradeData datafiles/FinalData datafiles/TradeDetails logs misc
RUN chown -R backtestuser:backtestuser datafiles logs misc

# Switch away from root access safely now that paths and permissions are assigned
USER backtestuser

ENTRYPOINT ["python", "./UpstoxBackTestManager_cls.py"]
