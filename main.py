import urllib
import mimetypes
import re
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from pathlib import Path

host_name = 'localhost'
host_port = 8232


class HttpHandler(BaseHTTPRequestHandler):
    text_suffix = '&trade;'
    url_prefix = 'https://habr.com'
    encoding = "utf-8"
    htmlParser = 'html.parser'
    default_article = 'ru/company/yandex/blog/258673/'

    def do_GET(self):
        try:
            uri = self.url_prefix + (self.path + self.default_article if self.path == '/' else self.path)
            with urllib.request.urlopen(uri) as response:
                data = response.read()
                content_type = mimetypes.MimeTypes().guess_type(os.path.basename(uri).split('?')[0])[0]
                self.send_response(200)
                self.end_headers()

                if Path(uri).suffix == '':
                    content_type = 'text/html'
                    html_text = self.process_html(data.decode(self.encoding))
                    html_text = self.process_links(html_text)
                    self.wfile.write(html_text.encode(self.encoding))
                else:
                    self.wfile.write(data)

                self.send_header('Content-type', content_type)
        except urllib.error as e:
            print(e)

    @staticmethod
    def process_html(html):
        soup = BeautifulSoup(html, HttpHandler.htmlParser)
        main_div = soup.find('div', {'class': 'js-mediator-article'})

        for text in main_div.find_all(text=True):
            fixed_text = text
            for text_parts_item in fixed_text.split(' '):
                pattern = text_parts_item + HttpHandler.text_suffix
                if len(text_parts_item.strip()) == 6 and fixed_text.find(pattern) == -1:
                    fixed_text = re.sub(r'(^|\s+)(' + re.escape(text_parts_item) + r')(\s+|$)', r'\1' + r'\2' +
                                        HttpHandler.text_suffix + r'\3', fixed_text)
            text.replace_with(BeautifulSoup(fixed_text, HttpHandler.htmlParser))
        return str(soup)

    @staticmethod
    def process_links(html):
        soup = BeautifulSoup(html, HttpHandler.htmlParser)

        for link in soup.findAll('a', attrs={'href': re.compile('^' + HttpHandler.url_prefix)}):
            o = urlparse(link.get('href'))
            link["href"] = o.path

        for link in soup.findAll('use'):
            o = urlparse(link.get('xlink:href'))
            link["xlink:href"] = o.path

        return str(soup)


if __name__ == '__main__':
    server = HTTPServer((host_name, host_port), HttpHandler)
    print('Server started on {}:{}'.format(host_name, host_port))
    server.serve_forever()
