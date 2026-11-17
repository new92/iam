FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 IAM_HOME=/home/iam/.config/iam
RUN useradd --create-home --shell /bin/sh iam
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY iam ./iam
RUN python -m pip install --no-cache-dir .
USER iam
VOLUME ["/home/iam/.config/iam"]
ENTRYPOINT ["iam"]
CMD ["--help"]
