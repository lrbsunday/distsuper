from distsuper.common import tools


class TestTools(object):
    def test_char_length(self):
        assert tools.char_length("测试123") == 7
        assert tools.char_length("abc") == 3
        assert tools.char_length("中文") == 4

    def test_unicode_count(self):
        assert tools.unicode_count("测试123") == 2
        assert tools.unicode_count("abc") == 0
        assert tools.unicode_count("中文") == 2
