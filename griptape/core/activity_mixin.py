import inspect
from typing import Optional
from attr import define, field
from jinja2 import Template
from schema import Schema, Literal


@define
class ActivityMixin:
    ARTIFACTS_SCHEMA = {
        "artifacts": {
            "sources": [
                {
                    Literal(
                        "ramp_name",
                        description="Name of the ramp that should be used to load artifacts into the tool"
                    ): str,
                    Literal(
                        "artifact_names",
                        description="Names of the artifacts to load from the ramp and pass to the tool"
                    ): []
                }
            ]
        }
    }

    allowlist: Optional[list[str]] = field(default=None, kw_only=True)
    denylist: Optional[list[str]] = field(default=None, kw_only=True)

    @allowlist.validator
    def validate_allowlist(self, _, allowlist: Optional[list[str]]) -> None:
        if self.denylist is not None and allowlist is not None:
            raise ValueError("can't have both allowlist and denylist specified")

    @denylist.validator
    def validate_allowlist(self, _, denylist: Optional[list[str]]) -> None:
        if self.allowlist is not None and denylist is not None:
            raise ValueError("can't have both allowlist and denylist specified")

    @property
    def schema_template_args(self) -> dict:
        return {}

    # This method has to remain a method and can't be decorated with @property because
    # of the max depth recursion issue in `inspect.getmembers`.
    def activities(self) -> list[callable]:
        methods = []

        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            allowlist_condition = self.allowlist is None or name in self.allowlist
            denylist_condition = self.denylist is None or name not in self.denylist

            if getattr(method, "is_activity", False) and allowlist_condition and denylist_condition:
                methods.append(method)

        return methods

    def find_activity(self, name: str) -> Optional[callable]:
        for method in self.activities():
            if getattr(method, "is_activity", False) and method.config["name"] == name:
                return method

        return None

    def activity_name(self, activity: callable) -> str:
        if activity is None or not getattr(activity, "is_activity", False):
            raise Exception("This method is not an activity.")
        else:
            return activity.config["name"]

    def activity_description(self, activity: callable) -> str:
        if activity is None or not getattr(activity, "is_activity", False):
            raise Exception("This method is not an activity.")
        else:
            return Template(activity.config["description"]).render(self.schema_template_args)

    def activity_schema(self, activity: callable) -> Optional[dict]:
        if activity is None or not getattr(activity, "is_activity", False):
            raise Exception("This method is not an activity.")
        elif activity.config["schema"]:
            full_schema = {
                "input": activity.config["schema"].schema if activity.config["schema"] else {}
            }

            if self.should_pass_artifacts(activity):
                full_schema.update(self.ARTIFACTS_SCHEMA)

            return Schema(full_schema).json_schema("InputSchema")
        else:
            if self.should_pass_artifacts(activity):
                return Schema(self.ARTIFACTS_SCHEMA).json_schema("InputSchema")
            else:
                return None

    def should_pass_artifacts(self, activity: callable) -> bool:
        if activity is None or not getattr(activity, "is_activity", False):
            raise Exception("This method is not an activity.")
        else:
            return activity.config.get("pass_artifacts", False)
