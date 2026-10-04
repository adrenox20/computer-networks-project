#!/bin/bash

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

openssl genrsa -out "$DIR/app.team1.test.key" 2048

openssl req -new \
  -key "$DIR/app.team1.test.key" \
  -out "$DIR/app.team1.test.csr" \
  -config "$DIR/san.cnf"

openssl x509 -req \
  -in "$DIR/app.team1.test.csr" \
  -CA "$DIR/team1-ca.crt" \
  -CAkey "$DIR/team1-ca.key" \
  -CAcreateserial \
  -out "$DIR/app.team1.test.crt" \
  -days 825 \
  -sha256 \
  -extensions req_ext \
  -extfile "$DIR/san.cnf"

chmod 600 "$DIR/app.team1.test.key"

echo "Server certificate created:"
echo "$DIR/app.team1.test.crt"