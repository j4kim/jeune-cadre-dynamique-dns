#!/usr/bin/env python3
import base64
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_FILENAME = ".env"
LAST_IP_FILENAME = ".last_ip"
PUBLIC_IP_URL = "https://api.ipify.org"
INFOMANIAK_BASE_URL = "https://infomaniak.com/nic/update"


def get_public_ip() -> str:
    response = requests.get(PUBLIC_IP_URL)
    response.raise_for_status()
    ip = response.text.strip()
    if not ip:
        raise RuntimeError("Empty public IP response")
    return ip


def load_last_ip(storage_path: Path) -> str | None:
    if not storage_path.exists():
        return None
    return storage_path.read_text(encoding="utf-8").strip() or None


def save_last_ip(storage_path: Path, ip: str) -> None:
    storage_path.write_text(ip + "\n", encoding="utf-8")


def update_infomaniak(username: str, password: str, hostname: str, ip: str) -> str:
    response = requests.post(
        INFOMANIAK_BASE_URL,
        params={"hostname": hostname, "myip": ip},
        auth=(username, password),
    )
    response.raise_for_status()
    body = response.text.strip()
    if not body:
        raise RuntimeError("Empty response from Infomaniak update API")
    if not (body.startswith("good") or body.startswith("nochg")):
        raise RuntimeError(f"Infomaniak update failed: {body}")
    return body


def send_email(
    smtp_host: str,
    smtp_port: int,
    smtp_username: str | None,
    smtp_password: str | None,
    smtp_from: str,
    recipient: str,
    subject: str,
    body: str,
    use_tls: bool,
    use_ssl: bool,
) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_from
    message["To"] = recipient
    message.set_content(body)

    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            if use_tls:
                server.starttls(context=context)
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(message)


def main() -> int:
    root = Path(__file__).resolve().parent
    env_path = Path(os.environ.get("ENV_PATH", root / ENV_FILENAME))
    if not env_path.exists():
        print(f"Environment file not found: {env_path}", file=sys.stderr)
        return 1

    load_dotenv(dotenv_path=env_path)

    required = [
        "INFOMANIAK_USERNAME",
        "INFOMANIAK_PASSWORD",
        "INFOMANIAK_HOSTNAME",
        "SMTP_HOST",
        "SMTP_PORT",
        "EMAIL_TO",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"Missing required environment values: {', '.join(missing)}", file=sys.stderr)
        return 1

    inf_username = os.environ["INFOMANIAK_USERNAME"]
    inf_password = os.environ["INFOMANIAK_PASSWORD"]
    hostname = os.environ["INFOMANIAK_HOSTNAME"]
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.environ["SMTP_PORT"])
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_username or f"dyn-dns@{hostname}")
    recipient = os.environ["EMAIL_TO"]
    use_tls = os.getenv("SMTP_USE_TLS", "true") == "true"
    use_ssl = os.getenv("SMTP_USE_SSL", "false") == "true"
    last_ip_path = root / os.getenv("LAST_IP_FILE", LAST_IP_FILENAME)

    try:
        current_ip = get_public_ip()
    except Exception as exc:
        print(f"Error fetching public IP: {exc}", file=sys.stderr)
        return 1

    previous_ip = load_last_ip(last_ip_path)
    if previous_ip == current_ip:
        print(f"No change: public IP remains {current_ip}")
        return 0

    print(f"Public IP changed: {previous_ip or '<none>'} -> {current_ip}")

    try:
        update_result = update_infomaniak(inf_username, inf_password, hostname, current_ip)
        print(f"Infomaniak update response: {update_result}")
    except Exception as exc:
        print(f"Error updating Infomaniak: {exc}", file=sys.stderr)
        return 1

    subject = f"DynDNS IP changed for {hostname}"
    body = (
        f"Votre adresse IP publique a changé.\n"
        f"Nom d'hôte: {hostname}\n"
        f"Nouvelle IP: {current_ip}\n"
        f"Ancienne IP: {previous_ip or 'aucune'}\n"
        f"Réponse Infomaniak: {update_result}\n"
    )

    try:
        send_email(
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_username=smtp_username,
            smtp_password=smtp_password,
            smtp_from=smtp_from,
            recipient=recipient,
            subject=subject,
            body=body,
            use_tls=use_tls,
            use_ssl=use_ssl,
        )
        print(f"Notification envoyée à {recipient}")
    except Exception as exc:
        print(f"Erreur d'envoi du mail: {exc}", file=sys.stderr)
        return 1

    try:
        save_last_ip(last_ip_path, current_ip)
    except Exception as exc:
        print(f"Erreur lors de l'enregistrement de l'IP: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
