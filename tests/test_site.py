import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lxml import etree as ET, html

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from catalogue import ROOT, NS, LANG, q, read, records, record_view, schema, parser, entry_tree
from build import WORDS, build, render, repository_url
from export_csv import listed_rows, export
from list_summary import render_summary

REPOSITORY = 'https://github.com/example/nihu-database-directory'


def semantic(node):
    return node.tag, tuple(sorted(node.attrib.items())), (node.text or '').strip(), tuple(semantic(c) for c in node)


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = read(ROOT / 'data/databases.xml').getroot()

    def test_current_xml_and_csv_are_consistent_without_intake_history(self):
        listed = records(self.root, True)
        self.assertTrue(listed)
        self.assertEqual(len(listed), len(records(self.root)))
        official = ET.XMLSchema(ET.parse(str(ROOT / 'schema/jpcoar_scm.xsd'), parser()))
        for rec in listed:
            official.assertValid(rec.find(q('jpcoar:jpcoar')))
            self.assertFalse(rec.findall(q('nihu:csvRow')))
            admin = json.loads(rec.find(q('nihu:administration')).text)
            self.assertEqual(set(admin), {'website', 'csv_fields'})
            self.assertTrue(set(admin['website']) <= {'source_url','details'})
        with (ROOT / 'data/databases.csv').open(encoding='utf-8-sig', newline='') as handle:
            self.assertEqual(list(csv.DictReader(handle)), listed_rows(self.root))
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'export.csv'; export(self.root,path)
            self.assertEqual(path.read_bytes(),(ROOT/'data/databases.csv').read_bytes())

    def test_build_is_reproducible_and_publishes_only_standard_xml(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'site'
            build(ROOT/'data/databases.xml',output,REPOSITORY)
            first={str(p.relative_to(output)):p.read_bytes() for p in output.rglob('*') if p.is_file()}
            build(ROOT/'data/databases.xml',output,REPOSITORY)
            self.assertEqual(first,{str(p.relative_to(output)):p.read_bytes() for p in output.rglob('*') if p.is_file()})
            self.assertEqual(sorted(p.name for p in (output/'data').iterdir()),['jpcoar.xml'])
            pure=ET.parse(str(output/'data/jpcoar.xml'))
            self.assertEqual([semantic(n) for n in pure.findall('record/metadata/jpcoar:jpcoar',NS)],
                             [semantic(r.find(q('jpcoar:jpcoar'))) for r in records(self.root,True)])
            self.assertFalse(pure.xpath('//*[namespace-uri()=$uri]',uri=NS['nihu']))
            for page in [output/'index.html',output/'en/index.html']:
                doc=html.fromstring(page.read_bytes())
                links=doc.xpath('//footer//nav/a/@href')
                self.assertEqual(links, ['./data/jpcoar.xml' if page.parent==output else '../data/jpcoar.xml',REPOSITORY])
                for node in doc.xpath('//link[@href]|//script[@src]|//img[@src]'):
                    url=node.get('href') or node.get('src')
                    if url.startswith(('./','../')):
                        self.assertTrue((page.parent/url).is_file(),url)

    def test_search_controls_and_modal_text_are_available_in_both_languages(self):
        for lang, label in [('ja','名称・説明・機関名から検索'),('en','Search names, descriptions and institutes')]:
            with self.subTest(lang=lang):
                doc=html.fromstring(render(self.root,lang,REPOSITORY))
                self.assertFalse(doc.xpath('//*[@data-language-switch]'))
                field=doc.get_element_by_id('directory-query')
                self.assertEqual(field.get('type'),'search')
                self.assertEqual(field.get('placeholder'),label)
                self.assertFalse(doc.xpath('//*[@id="clear-search"]'))
                self.assertEqual(doc.xpath('//label[@for="directory-query"]/@class'),['sr-only'])
                self.assertEqual(doc.xpath('//label[@for="directory-query"]/text()'),[label])
                self.assertEqual(field.get('aria-describedby'),'search-help')
                self.assertEqual(doc.get_element_by_id('search-status').get('role'),'status')
                for rec in records(self.root,True):
                    view=record_view(rec,lang)
                    detail=doc.get_element_by_id('detail-'+view['id'])
                    description=detail.xpath('.//div[@class="dialog-overview"]/p')[0]
                    self.assertEqual(''.join(description.text_content().splitlines()),
                                     ''.join((view['description'] or WORDS[lang]['no_description']).splitlines()))

    def test_hierarchy_uses_either_standard_relation_direction(self):
        expected=render(self.root,'ja',REPOSITORY)
        for kind in ['hasPart','isPartOf']:
            changed=copy.deepcopy(self.root)
            for rec in records(changed):
                meta=rec.find(q('jpcoar:jpcoar'))
                for rel in list(meta.findall(q('jpcoar:relation'))):
                    if rel.get('relationType')==kind:meta.remove(rel)
            self.assertEqual(render(changed,'ja',REPOSITORY),expected)
        def v(rid,rel=(),ids=None):
            return dict(id=rid,institution='nihu',order=0,identifiers=ids or ['https://example.org/'+rid],
                        relations=list(rel),has_parts=any(k=='hasPart' for k,u in rel),list_summary='')
        shared=[v('a',ids=['https://example.org/shared']),v('b',ids=['https://example.org/shared'])]
        self.assertEqual(len(entry_tree(shared)),2)
        with self.assertRaisesRegex(ValueError,'Ambiguous'):
            entry_tree(shared+[v('p',[('hasPart','https://example.org/shared')])])
        with self.assertRaisesRegex(ValueError,'Cyclic'):
            entry_tree([v('a',[('hasPart','https://example.org/b')]),v('b',[('isPartOf','https://example.org/b')])])
        external=[v('a',[('hasPart','https://elsewhere.example.org/b')])]
        self.assertEqual(len(entry_tree(external)),1)

    def test_summaries_are_bounded_html_separate_from_modal_abstract(self):
        self.assertIn('<strong>visible</strong>',render_summary('<p><strong>visible</strong></p>'))
        self.assertTrue(render_summary('<p>'+'字'*500+'</p>'))
        for value in ['<p>'+'字'*501+'</p>','<script>alert(1)</script>','<p onclick="x()">x</p>',
                      '<a href="jav&#97;script:alert(1)">x</a>','<img src=x>','<p style="color:red">x</p>']:
            with self.subTest(value=value[:50]), self.assertRaises(ValueError):render_summary(value)
        changed=copy.deepcopy(self.root)
        rec=next(r for r in records(changed) if r.find(q('nihu:listSummary')) is not None)
        summary=rec.find(q('nihu:listSummary')); summary.set(LANG,'ja'); summary.text='<p>LIST-ONLY <strong>HTML</strong></p>'
        for duplicate in list(rec.findall(q('nihu:listSummary')))[1:]:
            if duplicate.get(LANG)=='ja':rec.remove(duplicate)
        meta=rec.find(q('jpcoar:jpcoar'))
        abstract=next(n for n in meta.findall(q('datacite:description')) if n.get(LANG)=='ja')
        abstract.text='MODAL-ONLY DESCRIPTION'
        doc=html.fromstring(render(changed,'ja',REPOSITORY))
        item=doc.xpath('//li[@data-entry=$id]',id=rec.get('id'))[0]
        self.assertEqual(item.xpath('./div[@class="list-summary"]//strong/text()'),['HTML'])
        detail=doc.xpath('//template[@id=$id]',id='detail-'+rec.get('id'))[0]
        self.assertIn('MODAL-ONLY DESCRIPTION',detail.text_content())
        self.assertNotIn('LIST-ONLY',detail.text_content())

    def test_standard_metadata_edits_drive_display_and_csv(self):
        changed=copy.deepcopy(self.root);rec=records(changed,True)[0];meta=rec.find(q('jpcoar:jpcoar'))
        title=meta.find(q('dc:title'));title.text='<img src=x onerror="alert(1)"> & edited'
        target=meta.find(q('jpcoar:identifier'));position=list(meta).index(target)
        for old in meta.findall(q('jpcoar:identifier')):meta.remove(old)
        target=ET.Element(q('jpcoar:identifier'),identifierType='URI');target.text='https://example.org/new-url';meta.insert(position,target)
        output=render(changed,'ja',REPOSITORY)
        self.assertNotIn('<img src=x',output);self.assertIn('&lt;img src=x',output)
        self.assertEqual(record_view(rec,'ja')['url'],target.text)
        self.assertEqual(listed_rows(changed)[0]['Japanese Title'],title.text)

    def test_build_needs_no_research_or_json_source_files(self):
        original=Path.read_text
        def guard(path,*args,**kwargs):
            if path.suffix=='.json':raise AssertionError(f'Unexpected JSON source: {path}')
            return original(path,*args,**kwargs)
        with tempfile.TemporaryDirectory() as temp, patch.object(Path,'read_text',guard):
            build(ROOT/'data/databases.xml',Path(temp)/'site',REPOSITORY)
        for name in ['sources','snapshots','tools/apply_review.py','tools/prepare.py','tools/review_sources.py']:
            self.assertFalse((ROOT/name).exists(),name)

    def test_invalid_input_does_not_replace_existing_output(self):
        changed=copy.deepcopy(self.root)
        rec=next(r for r in records(changed) if r.find(q('nihu:listSummary')) is not None)
        summary=next(n for n in rec.findall(q('nihu:listSummary')) if n.get(LANG)=='en');summary.text='<p>'+'x'*501+'</p>'
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'bad.xml';source.write_bytes(ET.tostring(changed));output=Path(temp)/'site';output.mkdir();(output/'index.html').write_text('existing')
            with self.assertRaises(ValueError):build(source,output,REPOSITORY)
            self.assertEqual((output/'index.html').read_text(),'existing')
            source.write_text('<!DOCTYPE x [<!ENTITY x SYSTEM "file:///not-a-file">]><x>&x;</x>')
            with self.assertRaises(ValueError):read(source)

    def test_actions_repository_sets_the_github_link(self):
        with patch.dict('os.environ',{'GITHUB_REPOSITORY':'owner/directory'}):
            self.assertEqual(repository_url(),'https://github.com/owner/directory')
            self.assertEqual(repository_url(REPOSITORY),REPOSITORY)
        with self.assertRaises(ValueError):repository_url('javascript:alert(1)')


if __name__=='__main__':unittest.main()
