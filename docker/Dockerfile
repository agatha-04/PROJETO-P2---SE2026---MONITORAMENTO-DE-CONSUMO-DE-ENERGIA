FROM python:3.12.15-slim-bookworm
RUN useradd --system --uid 1000 --no-create-home --shell /usr/sbin/nologin app \
 && mkdir /data && chown app /data
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY coletor.py web.py healthcheck.py ./
COPY templates ./templates
ENV PYTHONUNBUFFERED=1 DB_PATH=/data/energia.db HWMON_GLOB=/ina/hwmon/hwmon*
USER app
EXPOSE 5000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 CMD ["python", "healthcheck.py", "web"]
CMD ["python", "web.py"]
