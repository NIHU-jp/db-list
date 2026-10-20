#!/usr/bin/env python3
"""SSG: validated XML -> standalone HTML, assets and downloadable data. Offline."""
import argparse
import copy
import html
import json
import os
import shutil
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

from lxml import etree as ET

from catalogue import ROOT, NS, q, read, records, record_view, institutions, safe_url, write, entry_tree, resource_counts, relation_graph

WORDS = {
 'ja': dict(page_title='NIHU各機関 データベース・データセット 一覧', heading='NIHU各機関 データベース・データセット 一覧',
  meta_description='人間文化研究機構の6機関と本部が提供するデータベースを、機関別に探せます。',
  intro='歴史、文学、言語、文化、環境、民族。<br>人間文化研究機構の6機関と本部が提供するデータベースをご案内します。',
  stat_label='データベース', hero_note='6機関データベースリンク ＋ 本部', updated_label='一覧確認日',
  skip_label='本文へ移動', home_label='データベース一覧', language_label='言語とサイト案内', portal_label='機構ポータル',
  other_lang='en', finder_label='データベースを探す', search_label='名称・説明・機関名から検索',
  search_help='詳細画面の説明文も検索します。空白で区切ると、すべての語を含む項目を表示します。',
  search_placeholder='名称・キーワードから探す', clear_label='検索語を消す', filter_label='機関で絞り込む',
  results_label='データベース一覧', count_template='{visible} / {total} 件',
  empty_title='該当するデータベースがありません', empty_description='検索語や機関の選択を変えてお試しください。', reset_label='絞り込みを解除',
  note_title='この一覧について', note_text='名称を選ぶと概要を確認できます。「データベースを見る」から、各機関の公開サイトへ移動します。',
  footer_label='6機関と本部のデータベース', data_label='データと出典', xml_label='JPCOAR XML', original_label='掲載元の一覧',
  footer_note='人間文化研究機構の公開一覧をもとに作成。各データベースの利用条件は、リンク先をご確認ください。',
  detail_label='DATABASE DETAILS', close_label='詳細を閉じる', noscript_note='JavaScriptが無効のため、名称のリンクからデータベースへ直接移動します。',
  all_label='すべて', visit_label='データベースを見る', overview='概要', alternate='英語名称', source_label='掲載元の説明',
  help_label='ヘルプ', breadcrumb_label='現在の位置', top_label='トップページ',
  all_count_prefix='全 ', list_count_prefix='データベース一覧（', count_suffix=' 件', mobile_count_end='）',
  nihu_lang='ja', nihu_logo='jp', nihu_name='人間文化研究機構',
  no_description='この項目の概要は未整備です。収録内容と利用条件は、提供元の公開サイトをご確認ください。',
  copy_label='この項目のリンクをコピー', copied_label='コピーしました', url_label='公開サイト', subjects_label='関連キーワード'),
 'en': dict(page_title='Databases and Datasets of NIHU Institutions', heading='Databases and Datasets of NIHU Institutions',
  meta_description='Explore databases from the six institutes and headquarters of the National Institutes for the Humanities.',
  intro='History, literature, language, culture, environment and ethnology.<br>Explore databases from the six institutes and headquarters of NIHU.',
  stat_label='DATABASES', hero_note='Six institutes. One place to explore.', updated_label='List checked',
  skip_label='Skip to content', home_label='database directory', language_label='Language and site navigation', portal_label='NIHU portal',
  other_lang='ja', finder_label='Find a database', search_label='Search names, descriptions and institutes',
  search_help='Includes descriptions in the detail dialogs. Separate words with spaces to match all of them.',
  search_placeholder='Search by name or keyword', clear_label='Clear search', filter_label='Filter by institution',
  results_label='Database directory', count_template='{visible} / {total} databases',
  empty_title='No databases found', empty_description='Try another keyword or select a different institution.', reset_label='Clear filters',
  note_title='Using this directory', note_text='Select a database name to read its overview, then choose “Visit database” to open the provider’s website.',
  footer_label='Databases from NIHU institutes', data_label='Data and sources', xml_label='JPCOAR XML', original_label='Original directory',
  footer_note='Based on the public NIHU directory. Please check each provider’s website for terms of use.',
  detail_label='DATABASE DETAILS', close_label='Close details', noscript_note='JavaScript is disabled. Database names link directly to the providers’ websites.',
  all_label='All', visit_label='Visit database', overview='Overview', alternate='Japanese title', source_label='Original description',
  help_label='Help', breadcrumb_label='Breadcrumb', top_label='Top',
  all_count_prefix='All ', list_count_prefix='See list (', count_suffix=' cases', mobile_count_end=')',
  nihu_lang='en', nihu_logo='en', nihu_name='National Institutes for the Humanities',
  no_description='An overview has not yet been prepared for this entry. Please visit the provider’s website for coverage and terms of use.',
  copy_label='Copy link to this entry', copied_label='Copied', url_label='Website', subjects_label='Keywords'),
}


def esc(value):
    return html.escape(str(value), quote=True)


def repository_url(value=''):
    """Resolve the repository link from an explicit URL, Actions, or Git origin."""
    if value:
        if not safe_url(value):
            raise ValueError('Repository URL must be HTTP(S)')
        return safe_url(value)
    slug = os.environ.get('GITHUB_REPOSITORY', '')
    if slug and len(slug.split('/')) == 2:
        return safe_url('https://github.com/' + slug)
    result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], cwd=ROOT,
                            capture_output=True, text=True)
    origin = result.stdout.strip()
    if origin.startswith('git@github.com:'):
        origin = 'https://github.com/' + origin.removeprefix('git@github.com:')
    return safe_url(origin.removesuffix('.git')) if origin else ''


def render(root, lang, repository=''):
    words = WORDS[lang]
    prefix = '.' if lang == 'ja' else '..'
    groups = institutions(root)
    entries = [record_view(rec, lang) for rec in records(root, listed=True)]
    tree = entry_tree(entries)
    by_id, children, parents = relation_graph(entries)

    def entry_link(entry):
        return f'<a href="{esc(entry["url"])}" data-open="{esc(entry["id"])}"><span class="item-title">{esc(entry["title"])}</span></a>'

    def item(node):
        entry, nested = node['entry'], node['children']
        content = entry_link(entry)
        if entry['list_summary']:
            content += f'<div class="list-summary">{entry["list_summary"]}</div>'
        if nested:
            children = '<ul class="database-children">' + ''.join(item(n) for n in nested) + '</ul>'
            if len(nested) > 20:
                label = '資料群を表示' if lang == 'ja' else 'Show collections'
                children = f'<details class="collection-list"><summary>{label}</summary>{children}</details>'
            content += children
        highlighted = bool(nested) or entry['has_parts'] or bool(entry['list_summary'])
        return f'<li class="database-item{" database-group" if highlighted else ""}" data-entry="{esc(entry["id"])}">{content}</li>'

    def related(entry):
        ids = parents[entry['id']] | children[entry['id']]
        if not ids:
            return ''
        nested = sorted((by_id[rid] for rid in ids), key=lambda e: (e['order'], e['id']))
        links = '<ul>' + ''.join(f'<li>{entry_link(e)}</li>' for e in nested) + '</ul>'
        if len(nested) > 20:
            label = '資料群を表示' if lang == 'ja' else 'Show collections'
            links = f'<details class="collection-list"><summary>{label}</summary>{links}</details>'
        return '<div class="dialog-relations">' + links + '</div>'
    counts = resource_counts(entries)
    sections, templates = [], []
    for number, institution in enumerate(groups, 1):
        code = institution['code']
        rows = [item(node) for node in tree if node['entry']['institution'] == code]
        ordered = sorted([e for e in entries if e['institution'] == code], key=lambda e: (e['order'], e['id']))
        for index, entry in enumerate(ordered, 1):
            other_title = f'<p class="dialog-alternate" lang="{words["other_lang"]}">{esc(entry["other_title"])}</p>' if entry['other_title'] else ''
            description = esc(entry['description'] or words['no_description']).replace('\n', '<br>')
            subjects = ''.join(f'<span>{esc(s)}</span>' for s in entry['subjects'])
            keywords = f'<div class="dialog-tags" aria-label="{words["subjects_label"]}">{subjects}</div>' if subjects else ''
            domain = urlsplit(entry['url']).netloc
            original = f'<a class="dialog-source" href="{esc(entry["source_url"])}">{words["source_label"]} ↗</a>' if entry['source_url'] else ''
            templates.append(f'''<template id="detail-{esc(entry['id'])}"><div class="dialog-institution"><span class="institution-dot inst-{esc(code)}"></span>{esc(institution[lang])}</div><h2 id="dialog-title">{esc(entry['title'])}</h2>{other_title}{related(entry)}<div class="dialog-overview"><h3>{words['overview']}</h3><p>{description}</p></div>{keywords}<a class="visit-button" href="{esc(entry['url'])}" target="_blank" rel="noopener noreferrer">{words['visit_label']}<span aria-hidden="true">↗</span></a><p class="destination">{esc(domain)}</p><div class="dialog-footer">{original}<button type="button" data-copy="{esc(entry['id'])}" data-copied-label="{words['copied_label']}">{words['copy_label']}</button></div></template>''')
        short_label = ('人文機構' if code == 'nihu' else institution['short']) if lang == 'ja' else institution['abbr']
        full_label = ('人間文化研究機構' if code == 'nihu' else institution['ja']) if lang == 'ja' else institution['en']
        sections.append(f'''<section class="institution-section inst-{esc(code)}" id="institution-{esc(code)}" data-section="{esc(code)}" aria-labelledby="heading-{esc(code)}"><div class="institution-heading"><div class="institution-logo"><img src="{prefix}/{esc(institution['logo'])}" alt="" width="80" height="80" loading="lazy"></div><div class="institution-titles"><h2 id="heading-{esc(code)}">{esc(short_label)}</h2><p>{esc(full_label)}</p></div></div><details class="institution-details" open><summary>{words['results_label']}<span class="disclosure-arrow" aria-hidden="true"></span></summary><ul class="database-list">{''.join(rows)}</ul></details></section>''')
    snapshot = datetime.fromisoformat(root.get('snapshot')).astimezone(timezone(timedelta(hours=9))).date().isoformat()
    total = sum(counts.values())
    values = dict(words, lang=lang, prefix=prefix, total=total,
                  repository_link=f'<a href="{esc(repository)}">GitHub ↗</a>' if repository else '',
                  home='./index.html',
                  snapshot=snapshot, sections=''.join(sections), details='\n'.join(templates),
                  initial_count=words['count_template'].format(visible=total, total=total))
    return Template((ROOT / 'templates/page.html').read_text()).substitute(values)


def build(input_path, output, repository=''):
    document = read(input_path)
    root = document.getroot()
    listed = records(root, listed=True)
    if not listed:
        raise ValueError('No listed records; refusing to replace the generated site')
    known = {i['code'] for i in institutions(root)}
    for rec in listed:
        view = record_view(rec, 'ja')
        if view['institution'] not in known or not view['url']:
            raise ValueError(f'Invalid listed record: {view["id"]}')
    # Validate both languages, including HTML summaries, before changing any files.
    repository = repository_url(repository)
    pages = {lang: render(root, lang, repository) for lang in ['ja', 'en']}
    output = Path(output)
    if output.resolve() == ROOT.resolve() or ROOT.resolve().is_relative_to(output.resolve()):
        raise ValueError('Output must not overwrite the source tree')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'en').mkdir(exist_ok=True)
    for lang, path in [('ja', output / 'index.html'), ('en', output / 'en/index.html')]:
        path.write_text(pages[lang])
    shutil.copytree(ROOT / 'assets', output / 'assets', dirs_exist_ok=True)
    (output / '.nojekyll').write_text('')
    (output / 'data').mkdir(exist_ok=True)
    # A familiar collection wrapper containing only standard JPCOAR metadata.
    pure = ET.Element('ListRecords', nsmap={k: v for k, v in NS.items() if k != 'nihu'})
    for rec in listed:
        metadata = ET.SubElement(ET.SubElement(pure, 'record'), 'metadata')
        metadata.append(copy.deepcopy(rec.find(q('jpcoar:jpcoar'))))
    ET.cleanup_namespaces(pure)
    write(pure, output / 'data/jpcoar.xml')
    # Only the standard XML is distributed by the website.
    for legacy in ['catalogue.xml', 'databases.xml', 'listed.csv', 'summary.json']:
        (output / 'data' / legacy).unlink(missing_ok=True)
    print(f'Built {len(listed)} database entries in Japanese and English → {output}')


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--input', type=Path, default=ROOT / 'data/databases.xml')
    args.add_argument('--output', type=Path, default=ROOT / 'dist')
    args.add_argument('--repository-url', default='', help='GitHub URL; defaults to Actions environment or origin')
    opts = args.parse_args()
    build(opts.input, opts.output, opts.repository_url)


if __name__ == '__main__':
    main()
