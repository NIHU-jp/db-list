"""Shared, offline XML profile. JPCOAR is kept separate from local administration."""
import json
from pathlib import Path
from urllib.parse import quote, urlsplit

from lxml import etree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {
    'nihu': 'urn:nihu-local:database-catalogue:1',
    'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/2.0/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'datacite': 'https://schema.datacite.org/meta/kernel-4/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
}
LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def q(name):
    prefix, local = name.split(':')
    return f'{{{NS[prefix]}}}{local}'


def element(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, q(tag), {k: str(v) for k, v in attrs.items()})
    if text is not None:
        node.text = str(text)
    return node


def text(node, name, lang=None):
    matches = node.findall(name, NS)
    if lang is not None:
        matches = [n for n in matches if n.get(LANG) == lang]
    return (matches[0].text or '') if matches else ''


def safe_url(value):
    """Reject active schemes even if the XML itself is schema-valid."""
    value = value.strip()
    parts = urlsplit(value)
    return quote(value, safe=":/?#@!$&'()*+,;=%") if parts.scheme in ('http', 'https') and parts.hostname and not parts.username else ''


class LocalSchemaResolver(ET.Resolver):
    def resolve(self, url, public_id, context):
        if not url.endswith('.xsd'):
            return None
        filename = url.rsplit('/', 1)[-1]
        local = ROOT / 'schema' / filename
        if local.exists() and filename.endswith('.xsd'):
            return self.resolve_filename(str(local), context)
        raise ValueError(f'External schema resolution refused: {url}')


def parser():
    result = ET.XMLParser(resolve_entities=False, load_dtd=False, no_network=True,
                          remove_blank_text=True)
    result.resolvers.add(LocalSchemaResolver())
    return result


def schema():
    return ET.XMLSchema(ET.parse(str(ROOT / 'schema/catalogue.xsd'), parser()))


def read(path, validate=True):
    document = ET.parse(str(path), parser())
    if document.docinfo.doctype:
        raise ValueError('DTD is not supported')
    if validate:
        schema().assertValid(document)
    return document


def write(root, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if root.tag == q('nihu:catalogue') and root.nsmap.get('nihu') != NS['nihu']:
        import copy
        current = ET.Element(root.tag, attrib=root.attrib, nsmap=NS)
        current.extend(copy.deepcopy(child) for child in root)
        root = current
    path.write_bytes(ET.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True))


def institutions(root):
    return [dict(n.attrib) for n in root.findall('nihu:institutions/nihu:institution', NS)]


def records(root, listed=False):
    values = root.findall('nihu:records/nihu:record', NS)
    return [r for r in values if not listed or r.get('listed') == 'true']


def record_view(rec, lang):
    meta = rec.find('jpcoar:jpcoar', NS)
    admin = json.loads(text(rec, 'nihu:administration'))
    title = text(meta, 'dc:title', lang) or text(meta, 'dc:title')
    descriptions = meta.findall('datacite:description', NS)
    description = next((n.text or '' for n in descriptions if n.get(LANG) == lang and n.get('descriptionType') == 'Abstract'), '')
    other_lang = 'en' if lang == 'ja' else 'ja'
    website = admin.get('website') or {}
    urls = website.get('details', {})
    target = urls.get(lang, {}).get('url') or urls.get(other_lang, {}).get('url')
    metadata_urls = [safe_url(n.text or '') for n in meta.findall('jpcoar:identifier', NS) if safe_url(n.text or '')]
    # Language hints can select an existing identifier, never override the metadata.
    if safe_url(target or '') not in metadata_urls:
        target = next(iter(metadata_urls), '')
    from list_summary import render_summary
    summaries = rec.findall('nihu:listSummary', NS)
    languages = [n.get(LANG) for n in summaries]
    if len(languages) != len(set(languages)):
        raise ValueError(f'Duplicate listSummary language: {rec.get("id")}')
    rendered_summaries = {n.get(LANG): render_summary(n.text or '') for n in summaries}
    relations = [(r.get('relationType'), n.text or '')
                 for r in meta.findall(q('jpcoar:relation'))
                 for n in r.findall(q('jpcoar:relatedIdentifier'))
                 if r.get('relationType') in {'hasPart', 'isPartOf'}]
    return dict(id=rec.get('id'), institution=rec.get('institution', ''),
                order=int(rec.get('order', '0')), title=title,
                other_title=text(meta, 'dc:title', other_lang), description=description,
                other_description=next((n.text or '' for n in descriptions if n.get(LANG) == other_lang and n.get('descriptionType') == 'Abstract'), ''),
                url=safe_url(target or ''),
                source_url=safe_url(website.get('source_url', '')),
                subjects=[n.text or '' for n in meta.findall('jpcoar:subject', NS)],
                identifiers=[n.text or '' for n in meta.findall(q('jpcoar:identifier'))],
                relations=relations, list_summary=rendered_summaries.get(lang, ''),
                has_parts=any(kind == 'hasPart' for kind, uri in relations),
                admin=admin, meta=meta)


def relation_graph(entries):
    """Resolve explicit JPCOAR part relations against this input's identifiers."""
    by_id = {e['id']: e for e in entries}
    if len(by_id) != len(entries):
        raise ValueError('Duplicate entry IDs')
    index = {}
    for entry in entries:
        for identifier in entry['identifiers']:
            index.setdefault(identifier, set()).add(entry['id'])
    children = {identifier: set() for identifier in by_id}
    parents = {identifier: set() for identifier in by_id}
    for entry in entries:
        for kind, target in entry['relations']:
            if kind not in {'hasPart', 'isPartOf'}:
                continue
            matches = index.get(target, set())
            if len(matches) > 1:
                raise ValueError(f'Ambiguous part relation target: {target}')
            if not matches:
                continue  # External or unlisted resources remain metadata relations.
            related = next(iter(matches))
            parent, child = (entry['id'], related) if kind == 'hasPart' else (related, entry['id'])
            children[parent].add(child)
            parents[child].add(parent)
    visited, active = set(), set()
    def visit(identifier):
        if identifier in active:
            raise ValueError('Cyclic JPCOAR part relationships')
        if identifier in visited:
            return
        active.add(identifier)
        for child in children[identifier]:
            visit(child)
        active.remove(identifier)
        visited.add(identifier)
    for identifier in by_id:
        visit(identifier)
    return by_id, children, parents


def entry_tree(entries):
    """Build a hierarchy from either direction of the standard part relations."""
    by_id, children, parents = relation_graph(entries)
    def node(entry):
        nested = sorted((node(by_id[c]) for c in children[entry['id']]), key=lambda c: (c['order'], c['entry']['id']))
        return dict(entry=entry, children=nested, order=entry['order'])
    return sorted((node(e) for e in entries if not parents[e['id']]), key=lambda c: (
        not (bool(c['children']) or c['entry']['has_parts'] or c['entry']['list_summary']),
        c['order'], c['entry']['id']))


def resource_counts(entries):
    """Count unique leaf resources, excluding aggregates with resolved children."""
    by_id, children, parents = relation_graph(entries)
    from collections import Counter
    return Counter(e['institution'] for e in entries if not children[e['id']])
