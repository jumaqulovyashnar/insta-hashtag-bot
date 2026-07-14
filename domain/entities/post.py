from dataclasses import dataclass, field

@dataclass
class Post:
    shortcode: str
    url: str
    caption: str = ""
    comments: list[str] = field(default_factory=list)
