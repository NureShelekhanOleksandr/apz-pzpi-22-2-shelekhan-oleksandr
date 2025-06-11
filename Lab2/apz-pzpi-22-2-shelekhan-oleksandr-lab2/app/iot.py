import asyncio
import json
from cryptography.fernet import Fernet
from azure.iot.device import Message
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod, CloudToDeviceMethodResult
from app.core.config import settings
import uuid


class SmartLock:
    _registry_manager = None

    def __init__(self, device_id, encryption_key):
        self.device_id = device_id
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key)

    def get_registry_url(self):
        return f"HostName={settings.IOTHUB_HOST};SharedAccessKeyName={settings.REGISTRY_SHARED_ACCESS_KEY_NAME};SharedAccessKey={settings.REGISTRY_SHARED_ACCESS_KEY}"

    def registry_manager(self):
        if self._registry_manager is None:
            self._registry_manager = IoTHubRegistryManager.from_connection_string(
                self.get_registry_url()
            )
        return self._registry_manager

    def send_command(self, command):
        registry_manager = self.registry_manager()
        encrypted_command = self.cipher.encrypt(command.encode())
        msg = Message(json.dumps({"command": encrypted_command.decode()}))
        msg.message_id = uuid.uuid4()
        msg.content_encoding = "utf-8"
        msg.content_type = "application/json"
        device_method = CloudToDeviceMethod(method_name=command, payload=msg)
        response = registry_manager.invoke_device_method(self.device_id, device_method)
        return response


if __name__ == "__main__":
    # Використання класу
    lock_id = "5bb6e258:KPH2GIA1nFNTXAsr37/moDk604dm1jJQHr4nC59B4Bk="

    device_id = lock_id.split(":")[0]
    encryption_key = lock_id.split(":")[1].encode()

    smart_lock = SmartLock(device_id, encryption_key)
    smart_lock.send_command("open_lock")  # Відкрити замок
    smart_lock.send_command("close_lock")  # Закрити замок
    smart_lock.send_command("get_temperature")  # Отримати температуру
    smart_lock.send_command("get_temperature_stats")  # Отримати статистику температури
