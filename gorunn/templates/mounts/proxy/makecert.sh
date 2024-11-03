#/bin/bash

#Making certs
 openssl req \
  -x509 -nodes -days 3650 -newkey rsa:2048 \
  -subj "/CN=*local.gorunn.io" \
  -config openssl.cnf \
  -keyout certs/self/gorunn.key \
  -out certs/self/gorunn.crt
  echo "Adding to keychain"
  security add-trusted-cert -r trustRoot -k ~/Library/Keychains/login.keychain-db certs/self/gorunn.crt
