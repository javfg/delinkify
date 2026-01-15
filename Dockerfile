FROM python:3.14.2-alpine3.23
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

RUN apk add --no-cache ffmpeg deno

ARG UID=1000
ARG GID=1000

RUN addgroup -g ${GID} delinkify && \
    adduser -u ${UID} -G delinkify -h /home/delinkify -s /bin/sh -D delinkify

RUN mkdir -p /app && chown delinkify:delinkify /app

USER delinkify
WORKDIR /app
COPY --chown=delinkify:delinkify . .
RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "delinkify"]
