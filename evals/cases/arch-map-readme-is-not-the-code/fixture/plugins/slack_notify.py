"""Posts placed orders to the #orders Slack channel (webhook elided in this copy)."""


def on_event(event, payload):
    if event == "order_placed":
        pass  # post to Slack
