from __future__ import annotations

from typing import TYPE_CHECKING

from attr import define, field

from griptape.rules import Ruleset, Rule

if TYPE_CHECKING:
    from griptape.structures import Structure


@define(slots=False)
class RuleMixin:
    DEFAULT_RULESET_NAME = "Default Ruleset"
    ADDITIONAL_RULESET_NAME = "Additional Ruleset"

    rulesets: list[Ruleset] = field(factory=list, kw_only=True)
    rules: list[Rule] = field(factory=list, kw_only=True)
    structure: Structure = field(default=None, kw_only=True)

    @rulesets.validator  # pyright: ignore
    def validate_rulesets(self, _, rulesets: list[Ruleset]) -> None:
        if not rulesets:
            return

        if self.rules:
            raise ValueError("Can't have both rulesets and rules specified.")

    @rules.validator  # pyright: ignore
    def validate_rules(self, _, rules: list[Rule]) -> None:
        if not rules:
            return

        if self.rulesets:
            raise ValueError("Can't have both rules and rulesets specified.")

    @property
    def all_rulesets(self) -> list[Ruleset]:
        structure_rulesets = []

        if self.structure:
            if self.structure.rulesets:
                structure_rulesets = self.structure.rulesets
            elif self.structure.rules:
                structure_rulesets = [Ruleset(name=self.DEFAULT_RULESET_NAME, rules=self.structure.rules)]

        task_rulesets = []
        if self.rulesets:
            task_rulesets = self.rulesets
        elif self.rules:
            if structure_rulesets:
                task_ruleset_name = self.ADDITIONAL_RULESET_NAME
            else:
                task_ruleset_name = self.DEFAULT_RULESET_NAME

            task_rulesets = [Ruleset(name=task_ruleset_name, rules=self.rules)]

        return structure_rulesets + task_rulesets
