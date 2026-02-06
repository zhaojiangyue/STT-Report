class Plugin:
    name = "base"

    def __init__(self, config):
        self.config = config or {}

    def on_start(self, context):
        pass

    def on_report(self, context, report_type, report_path):
        pass

    def on_complete(self, context):
        pass


def load_plugins(plugin_names, plugin_config):
    plugins = []
    for name in plugin_names:
        if name == "email":
            from stt.plugins.email import EmailPlugin
            plugins.append(EmailPlugin(plugin_config.get("email", {})))
        elif name == "notion":
            from stt.plugins.notion import NotionPlugin
            plugins.append(NotionPlugin(plugin_config.get("notion", {})))
        elif name == "obsidian":
            from stt.plugins.obsidian import ObsidianPlugin
            plugins.append(ObsidianPlugin(plugin_config.get("obsidian", {})))
        elif name == "telegram":
            from stt.plugins.telegram import TelegramPlugin
            plugins.append(TelegramPlugin(plugin_config.get("telegram", {})))
    return plugins
