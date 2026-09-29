FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch first (~200 MB instead of several GB of CUDA libraries).
# Because it is installed here, the later requirements install sees torch
# as already satisfied and does not pull the CUDA build.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Download the Whisper model at build time so the first quiz request
# does not have to fetch ~460 MB.
RUN python -c "import whisper; whisper.load_model('small')"

COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--timeout", "600"]