FROM alpine:latest
RUN apk add --no-cache bash
COPY scripts/validate-env.sh /app/scripts/validate-env.sh
RUN chmod +x /app/scripts/validate-env.sh
CMD ["/app/scripts/validate-env.sh"]
