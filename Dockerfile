FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# install opencode
RUN curl -fsSL https://opencode.ai/install | bash
ENV PATH="/root/.opencode/bin:${PATH}"

# install python dependencies
RUN pip install --no-cache-dir fastapi uvicorn requests

# copy app
COPY adapter.py /app/adapter.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app
EXPOSE 80
CMD ["/app/entrypoint.sh"]
