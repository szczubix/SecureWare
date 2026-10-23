# Obraz statycznego panelu: docker build --build-arg PANEL=app|admin frontend/
FROM nginx:1.27-alpine
ARG PANEL
COPY ${PANEL}/ /usr/share/nginx/html/
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
# envsubst podstawia tylko API_ORIGIN (pozostale $zmienne w konfiguracji to zmienne nginx).
ENV NGINX_ENVSUBST_FILTER=^API_ORIGIN$
