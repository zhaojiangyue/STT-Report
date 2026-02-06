import requests

from stt.plugins.base import Plugin


class TelegramPlugin(Plugin):
    name = "telegram"

    def on_complete(self, context):
        token = self.config.get("bot_token")
        chat_id = self.config.get("chat_id")
        if not token or not chat_id:
            print("Telegram plugin missing bot_token or chat_id.")
            return
        text = f"STT report complete: {context.get('title')} | {context.get('output_dir')}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
