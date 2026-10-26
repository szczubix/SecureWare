# Kopie zapasowe: klient PostgreSQL 16 (zgodny z serwerem), age (szyfrowanie), Python + psycopg.
FROM postgres:16-alpine
RUN apk add --no-cache age python3 py3-psycopg tar \
    && adduser -D -u 10001 backup \
    && mkdir -p /backups /keys && chown backup:backup /backups /keys
COPY forvium_backup.py /usr/local/bin/forvium_backup.py
USER backup
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s \
    CMD ["python3", "/usr/local/bin/forvium_backup.py", "check"]
ENTRYPOINT ["python3", "/usr/local/bin/forvium_backup.py"]
CMD ["run"]
