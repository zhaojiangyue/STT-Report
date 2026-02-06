import smtplib
from email.mime.text import MIMEText

from stt.plugins.base import Plugin


class EmailPlugin(Plugin):
    name = "email"

    def on_complete(self, context):
        smtp_host = self.config.get("smtp_host")
        smtp_port = self.config.get("smtp_port", 587)
        username = self.config.get("username")
        password = self.config.get("password")
        to_addr = self.config.get("to")
        from_addr = self.config.get("from") or username
        if not all([smtp_host, username, password, to_addr]):
            print("Email plugin not configured (smtp_host/username/password/to).")
            return
        subject = self.config.get("subject", "STT Report Ready")
        body = f"Report complete for: {context.get('title')}\nOutput: {context.get('output_dir')}"
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
