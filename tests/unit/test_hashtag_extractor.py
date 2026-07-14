import unittest
from domain.services.hashtag_extractor import extract_hashtags
from domain.value_objects.hashtag import Hashtag

class TestHashtagExtractor(unittest.TestCase):
    def test_extract_latin_hashtags(self):
        text = "This is a post #rekda and #1m with some tags."
        tags = extract_hashtags(text)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0], Hashtag("rekda"))
        self.assertEqual(tags[1], Hashtag("1m"))

    def test_extract_cyrillic_hashtags(self):
        text = "Пост с тегами #мотивация и #лайк!"
        tags = extract_hashtags(text)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].value, "мотивация")
        self.assertEqual(tags[1].value, "лайк")

    def test_extract_multilingual_hashtags(self):
        text = "Chinese tag #今夜 and Arabic tag #العربية"
        tags = extract_hashtags(text)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].value, "今夜")
        self.assertEqual(tags[1].value, "العربية")

    def test_punctuation_stripping(self):
        text = "Hello #world, this is #test! Is #clean; or #parentheses(tag)"
        tags = extract_hashtags(text)
        self.assertEqual(len(tags), 4)
        self.assertEqual(tags[0].value, "world")
        self.assertEqual(tags[1].value, "test")
        self.assertEqual(tags[2].value, "clean")
        self.assertEqual(tags[3].value, "parentheses")

    def test_deduplication(self):
        text = "Repeated tags: #Tag, #tag, #TAG, #another"
        tags = extract_hashtags(text)
        self.assertEqual(len(tags), 2)
        self.assertEqual(tags[0].value, "Tag")
        self.assertEqual(tags[1].value, "another")
