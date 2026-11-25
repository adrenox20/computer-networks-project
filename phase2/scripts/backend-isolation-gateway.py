#!/usr/bin/env python3

import socket
import threading
import os
from datetime import datetime

ALLOWED_SOURCE = "10.7.20.185"

BACKENDS = {
    3001: ("127.0.0.1", 13001),
    3002: ("127.0.0.1", 13002),
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_FILE = os.path.join(
    BASE_DIR,
    "evidence/10-backend-isolation/isolation-gateway.log"
)


def log(message):
    line = f"[{datetime.now().isoformat()}] {message}"

    print(line, flush=True)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def relay(source, destination):
    try:
        while True:
            data = source.recv(65536)

            if not data:
                break

            destination.sendall(data)

    except Exception:
        pass


def handle_client(client, address, listen_port, target):

    source_ip = address[0]

    log(
        f"connection source={source_ip} "
        f"destination-port={listen_port}"
    )

    if source_ip != ALLOWED_SOURCE:

        log(
            f"DENIED source={source_ip} "
            f"destination-port={listen_port}"
        )

        client.close()
        return

    upstream_host, upstream_port = target

    log(
        f"ALLOWED source={source_ip} "
        f"destination-port={listen_port} "
        f"target={upstream_host}:{upstream_port}"
    )

    try:

        upstream = socket.create_connection(
            (upstream_host, upstream_port),
            timeout=5
        )

        client_to_backend = threading.Thread(
            target=relay,
            args=(client, upstream),
            daemon=True
        )

        backend_to_client = threading.Thread(
            target=relay,
            args=(upstream, client),
            daemon=True
        )

        client_to_backend.start()
        backend_to_client.start()

        client_to_backend.join()
        backend_to_client.join()

        upstream.close()

    except Exception as e:

        log(
            f"UPSTREAM ERROR "
            f"source={source_ip} "
            f"port={listen_port} "
            f"error={e}"
        )

    finally:
        client.close()


def listen_on_port(listen_port, target):

    server = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server.bind(("0.0.0.0", listen_port))

    server.listen(50)

    upstream_host, upstream_port = target

    log(
        f"LISTENING 0.0.0.0:{listen_port} "
        f"-> {upstream_host}:{upstream_port} "
        f"allowed-source={ALLOWED_SOURCE}"
    )

    while True:

        client, address = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client, address, listen_port, target),
            daemon=True
        )

        thread.start()


def main():

    log("Starting Phase 2 backend isolation gateway")

    for listen_port, target in BACKENDS.items():

        upstream_host, upstream_port = target

        log(
            f"BACKEND {listen_port} "
            f"-> {upstream_host}:{upstream_port}"
        )

    threads = []

    for listen_port, target in BACKENDS.items():

        thread = threading.Thread(
            target=listen_on_port,
            args=(listen_port, target),
            daemon=True
        )

        thread.start()

        threads.append(thread)

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
