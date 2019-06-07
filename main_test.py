import unittest
from main import HttpHandler


class TestMainMethods(unittest.TestCase):

    def test_if_html_process_is_correct(self):
        html = '<div class="js-mediator-article">Сейчас на фоне уязвимости Logjam все</div>'
        result = HttpHandler.process_html(html)
        self.assertTrue(result.find('™') > -1)

    def test_if_links_process_is_correct(self):
        html = '<a href="https://habr.com/ru/company/yandex/blog/258673/">link</a>'
        result = HttpHandler.process_links(html)
        self.assertTrue(result.find(HttpHandler.url_prefix) == -1)


if __name__ == '__main__':
    unittest.main()
