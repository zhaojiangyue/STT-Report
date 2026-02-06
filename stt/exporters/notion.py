def export_notion(text, config):
    try:
        from notion_client import Client
    except ImportError:
        print("notion-client not installed. Install with 'pip install notion-client'.")
        return
    token = config.get("token")
    database_id = config.get("database_id")
    if not token or not database_id:
        print("Notion export missing token or database_id in config.")
        return
    client = Client(auth=token)
    client.pages.create(
        parent={"database_id": database_id},
        properties={"Name": {"title": [{"text": {"content": "STT Report"}}]}},
        children=[{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": text[:2000]}}]}}],
    )
