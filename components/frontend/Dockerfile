FROM nginx:alpine

RUN apk add --no-cache gettext

COPY nginx.conf /etc/nginx/conf.d/default.conf.template

# Remove the base image's welcome page so the dashboard is the only index.
RUN rm /usr/share/nginx/html/index.html

COPY html/ /usr/share/nginx/html/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# Default proxy targets — override via environment variables
ENV API_BASE_URL="http://backend-api:5000/"
ENV NOTIFICATION_BASE_URL="http://notification-service:5002/"

# Substitute env vars into nginx config, then start nginx
CMD ["/bin/sh", "-c", "envsubst '${API_BASE_URL} ${NOTIFICATION_BASE_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]

EXPOSE 3000
