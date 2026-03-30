FROM python:3.12-slim

# System deps: git for cloning/committing, curl for gh CLI install
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && rm -rf /var/lib/apt/lists/*

# Install GitHub CLI (gh)
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Install dbt-snowflake (same version as the dbt container)
RUN pip install --no-cache-dir dbt-snowflake==1.9.1

WORKDIR /usr/app

# Install the agent package (same source as the agent container)
COPY agent/pyproject.toml agent/pyproject.toml
COPY agent/agent/ agent/agent/
RUN pip install --no-cache-dir ./agent

# Git identity for automated commits
RUN git config --global user.name "dbt-debugger-agent" \
    && git config --global user.email "agent@dbt-debugger"

# Stay alive for manual docker exec runs
ENTRYPOINT ["tail", "-f", "/dev/null"]
