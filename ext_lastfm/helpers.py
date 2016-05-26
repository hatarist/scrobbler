import re


def remove_html_tags(text):
    return re.compile(r'<[^>]+>').sub('', text)
