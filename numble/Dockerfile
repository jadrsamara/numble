# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.2
FROM python:${PYTHON_VERSION}-slim as base

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001

RUN pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
--mount=type=bind,source=requirements.txt,target=requirements.txt \
python -m pip install -r requirements.txt

# Copy the source code into the container.
COPY . .

# Expose the port that the application listens on.
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
