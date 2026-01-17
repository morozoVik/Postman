from django.test import TestCase

class BasicTest(TestCase):
    """Простой тест чтобы убедиться что тесты запускаются"""
    def test_basic(self):
        self.assertEqual(1 + 1, 2)