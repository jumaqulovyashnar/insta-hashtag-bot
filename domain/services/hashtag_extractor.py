import re
from domain.value_objects.hashtag import Hashtag

# Unicode-aware pattern: matches # followed by non-whitespace/non-punctuation characters
# This works for Latin, Cyrillic, Arabic, Asian scripts, etc.
HASHTAG_PATTERN = re.compile(r'#([^\s#.,!?;:()\'\"\[\]{}«»“”]+)', re.UNICODE)

def extract_hashtags(text: str) -> list[Hashtag]:
    """
    Pure function to extract unique hashtags from a given text.
    Preserves original case and order of first appearance.
    """
    if not text:
        return []
    
    matches = HASHTAG_PATTERN.findall(text)
    
    seen = set()
    unique_hashtags = []
    
    for val in matches:
        if not val:
            continue
        try:
            hashtag = Hashtag(val)
            norm_val = hashtag.value.lower()
            if norm_val not in seen:
                seen.add(norm_val)
                unique_hashtags.append(hashtag)
        except ValueError:
            continue
            
    return unique_hashtags
