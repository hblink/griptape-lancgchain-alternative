import re
from abc import ABC, abstractmethod
from typing import Optional

from attr import define, field, Factory
from griptape.tokenizers import TiktokenTokenizer


@define
class BaseChunker(ABC):
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "! ", "? ", " "]

    separators: list[str] = field(
        default=Factory(lambda self: self.DEFAULT_SEPARATORS, takes_self=True),
        kw_only=True
    )
    tokenizer: TiktokenTokenizer = field(
        default=TiktokenTokenizer(),
        kw_only=True
    )
    max_tokens_per_chunk: int = field(
        default=Factory(lambda self: self.tokenizer.max_tokens, takes_self=True),
        kw_only=True
    )

    @abstractmethod
    def chunk(self, *args, **kwargs) -> list[str]:
        ...

    def chunk_recursively(self, chunk: str, current_separator: Optional[str] = None) -> list[str]:
        token_count = self.tokenizer.token_count(chunk)

        if token_count <= self.max_tokens_per_chunk:
            return [chunk]
        else:
            balance_index = -1
            balance_diff = float("inf")
            tokens_count = 0
            half_token_count = token_count // 2

            if current_separator:
                separators = self.separators[self.separators.index(current_separator):]
            else:
                separators = self.separators

            for separator in separators:
                subchanks = list(filter(None, chunk.split(separator)))

                if len(subchanks) > 1:
                    for index, subchunk in enumerate(subchanks):
                        if index < len(subchanks):
                            subchunk = subchunk + separator

                        tokens_count += self.tokenizer.token_count(subchunk)

                        if abs(tokens_count - half_token_count) < balance_diff:
                            balance_index = index
                            balance_diff = abs(tokens_count - half_token_count)

                    first_subchunk = self.chunk_recursively(
                        (separator.join(subchanks[:balance_index + 1]) + separator).strip(),
                        separator
                    )
                    second_subchunk = self.chunk_recursively(
                        separator.join(subchanks[balance_index + 1:]).strip(),
                        separator
                    )

                    if first_subchunk and second_subchunk:
                        return first_subchunk + second_subchunk
                    elif first_subchunk:
                        return first_subchunk
                    elif second_subchunk:
                        return second_subchunk
                    else:
                        return []
            return []