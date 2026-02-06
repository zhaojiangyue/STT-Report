from stt.plugins.base import Plugin
from stt.exporters.notion import export_notion


class NotionPlugin(Plugin):
    name = "notion"

    def on_complete(self, context):
        report_text = context.get("primary_report_text")
        if not report_text:
            return
        export_notion(report_text, self.config)
