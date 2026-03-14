"""SMTP email composition and sending."""

import json
import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from smtplib import SMTPException, SMTPAuthenticationError, SMTPConnectError

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

SMTP_TIMEOUT = 15  # seconds

DEFAULT_CONFIG = {
    "smtp_server": "",
    "smtp_port": 587,
    "username": "",
    "password": "",
    # NOTE: Password is stored in plain text in config.json.
    # For production use, consider using keyring or encryption.
    "sender_name": "",
}


def load_smtp_config():
    """Load SMTP configuration from config.json."""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                config.update(loaded)
        except (json.JSONDecodeError, IOError):
            pass
    # Ensure port is int
    try:
        config["smtp_port"] = int(config.get("smtp_port", 587))
    except (ValueError, TypeError):
        config["smtp_port"] = 587
    return config


def save_smtp_config(config):
    """Save SMTP configuration to config.json."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def send_email(smtp_config, to_email, subject, body):
    """Send an email via SMTP. Returns (success: bool, message: str)."""
    if not smtp_config.get("smtp_server"):
        return False, "SMTP server not configured."
    if not smtp_config.get("username"):
        return False, "SMTP username not configured."
    if not to_email:
        return False, "Recipient email is required."
    if not subject:
        return False, "Subject is required."

    try:
        msg = MIMEMultipart()
        sender = smtp_config.get("username", "")
        sender_name = smtp_config.get("sender_name", "")
        if sender_name:
            msg["From"] = f"{sender_name} <{sender}>"
        else:
            msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_config["smtp_server"],
                               int(smtp_config["smtp_port"]),
                               timeout=SMTP_TIMEOUT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_config["username"], smtp_config["password"])
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully."
    except SMTPAuthenticationError:
        return False, "Authentication failed. Check username and password."
    except SMTPConnectError:
        return False, "Could not connect to SMTP server. Check server address and port."
    except socket.timeout:
        return False, "Connection timed out. Check server address and port."
    except socket.gaierror:
        return False, "Could not resolve SMTP server hostname."
    except SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_connection(smtp_config):
    """Test SMTP connection. Returns (success: bool, message: str)."""
    if not smtp_config.get("smtp_server"):
        return False, "SMTP server not configured."
    if not smtp_config.get("username"):
        return False, "SMTP username not configured."

    try:
        server = smtplib.SMTP(smtp_config["smtp_server"],
                               int(smtp_config["smtp_port"]),
                               timeout=SMTP_TIMEOUT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_config["username"], smtp_config["password"])
        server.quit()
        return True, "Connection successful."
    except SMTPAuthenticationError:
        return False, "Authentication failed. Check username and password."
    except SMTPConnectError:
        return False, "Could not connect to SMTP server. Check server address and port."
    except socket.timeout:
        return False, "Connection timed out. Check server address and port."
    except socket.gaierror:
        return False, "Could not resolve SMTP server hostname."
    except SMTPException as e:
        return False, f"SMTP error: {e}"
    except Exception as e:
        return False, f"Connection failed: {e}"
