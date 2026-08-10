FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Remove the base image's welcome page so the dashboard is the only index.
RUN rm /usr/share/nginx/html/index.html

COPY html/ /usr/share/nginx/html/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

EXPOSE 3000
