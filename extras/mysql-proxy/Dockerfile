FROM gliderlabs/alpine:3.3

RUN apk add --no-cache bash socat jq curl netcat-openbsd

COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 3306
