from dataclasses import dataclass

@dataclass(frozen=True)
class Usage:
    """Token counts for one model call."""
    prompt_tokens: int
    completion_tokens: int

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

