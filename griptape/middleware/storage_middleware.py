from __future__ import annotations
from typing import TYPE_CHECKING
from schema import Schema
from griptape.core.decorators import activity
from griptape.middleware import BaseMiddleware
from attr import define, field

if TYPE_CHECKING:
    from griptape.drivers import BaseStorageDriver


@define
class StorageMiddleware(BaseMiddleware):
    driver: BaseStorageDriver = field(kw_only=True)

    def process_output(self, tool_activity: callable, value: bytes) -> bytes:
        from griptape.utils import J2

        return J2("middleware/storage.j2").render(
            storage_name=self.name,
            tool_name=tool_activity.__self__.name,
            action_name=tool_activity.config["name"],
            key=self.driver.save(value)
        ).encode()

    @activity(config={
        "name": "load_data",
        "description": "Can be used to load data from the storage middleware",
        "schema": Schema(
            str,
            description="Artifact ID"
        )
    })
    def load_data(self, value: bytes) -> str:
        return self.driver.load(value.decode())