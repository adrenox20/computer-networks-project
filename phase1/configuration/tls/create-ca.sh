#!/bin/bash

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

openssl genrsa -out "$DIR/team1-ca.key" 2048

openssl req -x509 -new -nodes \
  -key "$DIR/team1-ca.key" \
  -sha256 \
  -days 3650 \
  -out "$DIR/team1-ca.crt" \
  -subj "/C=IN/ST=Haryana/L=Sonipat/O=Team1/CN=Team1 Local CA"

chmod 600 "$DIR/team1-ca.key"

echo "CA certificate created:"
echo "$DIR/team1-ca.crt"