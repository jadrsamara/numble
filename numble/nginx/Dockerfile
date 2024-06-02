FROM nginx:1.26

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
COPY certs/numble.one.chained.crt /etc/nginx/
COPY certs/numble.one.key /etc/nginx/


