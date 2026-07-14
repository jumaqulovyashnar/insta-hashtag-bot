class Hashtag:
    def __init__(self, value: str):
        # Strip leading '#' if present
        clean_value = value.lstrip('#').strip()
        if not clean_value:
            raise ValueError("Hashtag cannot be empty")
        self._value = clean_value

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, Hashtag):
            return False
        return self._value.lower() == other._value.lower()

    def __hash__(self):
        return hash(self._value.lower())

    def __str__(self):
        return f"#{self._value}"

    def __repr__(self):
        return f"Hashtag('{self._value}')"
