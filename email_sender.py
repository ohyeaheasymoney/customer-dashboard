"""SMTP email composition and sending."""

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "smtp_server": "",
    "smtp_port": 587,
    "username": "",
    "password": "",
    "sender_name": "",
}


def load_smtp_config():
    """Load SMTP configuration from config.json."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_smtp_config(config):
    """Save SMTP configuration to config.json."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def send_email(smtp_config, to_email, subject, body):
    """Send an email via SMTP. Returns (success: bool, message: str)."""
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

        server = smtplib.SMTP(smtp_config["smtp_server"], int(smtp_config["smtp_port"]))
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_config["username"], smtp_config["password"])
        server.sendmail(sender, to_email, msg.as_string())
        server.quit()
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Failed to send email: {e}"


def test_connection(smtp_config):
    """Test SMTP connection. Returns (success: bool, message: str)."""
    try:
        server = smtplib.SMTP(smtp_config["smtp_server"], int(smtp_config["smtp_port"]))
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_config["username"], smtp_config["password"])
        server.quit()
        return True, "Connection successful."
    except Exception as e:
        return False, f"Connection failed: {e}"
