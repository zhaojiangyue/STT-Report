import os

from stt.plugins.base import Plugin


class ObsidianPlugin(Plugin):
    name = "obsidian"

    def on_complete(self, context):
        vault = self.config.get("vault_path")
        if not vault:
            print("Obsidian plugin missing vault_path.")
            return
        os.makedirs(vault, exist_ok=True)
        title = context.get("title", "report")
        path = os.path.join(vault, f"{title}.md")
        text = context.get("primary_report_text", "")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
