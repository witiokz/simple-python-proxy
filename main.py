import copy
import html
import mimetypes
import os
import re
import urllib
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from string import punctuation
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen

from bs4 import BeautifulSoup, Comment

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
                self.send_header('Content-type', content_type if Path(uri).suffix != '' else content_type)
                self.end_headers()

                if Path(uri).suffix == '':
                    self.wfile.write(self.process(data).encode(self.encoding))
                else:
                    self.wfile.write(data)
        except HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(self.process(e.read()).encode(self.encoding))
        except Exception as e:
            print(e)

    @staticmethod
    def process(data):
        html_text = html.unescape(data.decode(HttpHandler.encoding))
        html_text = HttpHandler.process_html(html_text)
        html_text = HttpHandler.process_links(html_text)
        return html_text

    @staticmethod
    def process_html(html_text):
        soup = BeautifulSoup(html_text, HttpHandler.htmlParser)
        main_div = soup.find('body')
        punctuation_list = '|'.join([re.escape(x) for x in punctuation]).replace('/', '\\/')
        temp_data_list = []

        for script in soup(["script", "style"]):
            temp_data_list.append(copy.copy(script))
            script.decompose()

        for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            temp_data_list.append(copy.copy(comment))
            comment.extract()

        for text in main_div.find_all(text=True):
            fixed_text = text
            for text_parts_item in re.split("[\\s," + punctuation + "]", fixed_text):
                pattern = text_parts_item + HttpHandler.text_suffix
                if len(text_parts_item.strip()) == 6 and fixed_text.find(pattern) == -1:
                    fixed_text = re.sub(
                        r'(^|\s+|' + punctuation_list + ')(' + re.escape(text_parts_item) + r')(\s+|$|' +
                        punctuation_list + ')', r'\1' + r'\2' + HttpHandler.text_suffix + r'\3', fixed_text)
            text.replace_with(BeautifulSoup(fixed_text, HttpHandler.htmlParser))

        for item in temp_data_list:
            soup.body.append(item)

        return str(soup)

    @staticmethod
    def process_links(html_text):
        soup = BeautifulSoup(html_text, HttpHandler.htmlParser)

        for link in soup.findAll('a', attrs={'href': re.compile('^' + HttpHandler.url_prefix)}):
            o = urlparse(link.get('href'))
            link["href"] = o.path

        for link in soup.findAll('use'):
            o = urlparse(link.get('xlink:href'))
            link_value = o.path

            svg_hash_value = re.search(r'#(.*)', link.get('xlink:href'))
            if svg_hash_value:
                link_value = link_value + svg_hash_value.group()

            link["xlink:href"] = link_value

        return str(soup)


if __name__ == '__main__':
    server = HTTPServer((host_name, host_port), HttpHandler)
    print('Server started on {}:{}'.format(host_name, host_port))
    server.serve_forever()
