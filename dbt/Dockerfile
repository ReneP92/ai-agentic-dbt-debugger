FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Pin versions for reproducibility
RUN pip install --no-cache-dir \
    dbt-snowflake==1.9.1

WORKDIR /usr/app/dbt

# Copy the wrapper script into the image — it's infrastructure, not business logic.
# All dbt project files come in via bind mount at runtime.
COPY scripts/run_dbt.sh /usr/local/bin/run_dbt
RUN chmod +x /usr/local/bin/run_dbt

# Stay alive for manual docker exec runs
CMD ["tail", "-f", "/dev/null"]
