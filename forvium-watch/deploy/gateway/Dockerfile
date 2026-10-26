FROM nginx:1.27-alpine
COPY default.conf.template /etc/nginx/templates/default.conf.template
ENV NGINX_ENVSUBST_FILTER=^FORVIUM_
# Limity na adres IP klienta (deploy/loadtest/README.md). Klienci za NAT-em dziela jeden adres.
ENV FORVIUM_RATE_API=50r/s \
    FORVIUM_BURST_API=100 \
    FORVIUM_RATE_AUTH=10r/m
