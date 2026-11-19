class SystemAlertDispatcher:
    @staticmethod
    def dispatch_critical_notification(channel: str, message: str):
        """Routes text payloads to runtime system console channels or messaging links."""
        print(f"🔔 [{channel.upper()} ALERT]: {message}")
