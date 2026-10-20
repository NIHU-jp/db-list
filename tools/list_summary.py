"""Validate and render the bounded HTML fragment in nihu:listSummary."""
import html
from lxml import etree as ET, html as LH

MAX_TEXT_LENGTH = 500
MAX_SOURCE_LENGTH = 20000
TAGS = {'p', 'br', 'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'span',
        'table', 'caption', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
        'a', 'time', 'data'}
ATTRS = {'a': {'href', 'title'}, 'time': {'datetime'}, 'data': {'value'},
         'th': {'scope', 'colspan', 'rowspan'}, 'td': {'colspan', 'rowspan'}}


def render_summary(value):
    """Reject unsupported markup or overlong text; never truncate a fragment."""
    from catalogue import safe_url
    if not value:
        return ''
    if len(value) > MAX_SOURCE_LENGTH or '<!doctype' in value.lower() or '<!entity' in value.lower():
        raise ValueError('listSummary: unsupported declaration or excessive HTML source')
    try:
        root = LH.fragment_fromstring(value, create_parent='div', parser=LH.HTMLParser(no_network=True))
    except (ET.ParserError, ET.XMLSyntaxError) as exc:
        raise ValueError('listSummary: invalid HTML fragment') from exc
    for node in root.iterdescendants():
        if node.tag not in TAGS:
            raise ValueError(f'listSummary: unsupported HTML tag {node.tag}')
        for name, content in node.attrib.items():
            if name not in ATTRS.get(node.tag, set()) | {'lang'}:
                raise ValueError(f'listSummary: unsupported HTML attribute {name}')
            if name == 'href' and not safe_url(content):
                raise ValueError('listSummary: href must be an HTTP(S) URL')
            if name in {'rowspan', 'colspan'} and (not content.isdecimal() or not 1 <= int(content) <= 100):
                raise ValueError('listSummary: invalid table span')
        if node.tag == 'a' and 'href' in node.attrib:
            node.set('href', safe_url(node.get('href')))
    visible = ' '.join(' '.join(root.itertext()).split())
    if len(visible) > MAX_TEXT_LENGTH:
        raise ValueError(f'listSummary: {len(visible)} visible characters exceeds {MAX_TEXT_LENGTH}')
    return html.escape(root.text or '', quote=False) + ''.join(
        LH.tostring(child, encoding='unicode', method='html') for child in root)
