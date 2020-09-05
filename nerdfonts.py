import re
import urllib.request
import json
import fontforge
import xml.dom.minidom 
from functools import reduce

resources = {
    'fontfile': {
        'url': 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/src/glyphs/Symbols-2048-em%20Nerd%20Font%20Complete.ttf',
        'filepath': 'nerdfonts/Symbols-2048-em_Nerd_Font_Complete.ttf'
        },
    'cssfile': {
        'url': 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/css/nerd-fonts-generated.css',
        'filepath': 'nerdfonts/nerd-fonts-generated.css'
        }
    }

def download_resources():
    for (name, resource) in resources.items():
        print('Downloading', name, ':', resource['url'])
        urllib.request.urlretrieve(resource['url'], resource['filepath'])
        print('Saved', name, ':', resource['filepath'])


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def combine_dict(a, b):
    return {**a, **b}


def combine_tables(*tables):
    result = {}
    keys = set([key for table in tables for key in table.keys()])

    for key in keys:
        result[key] = reduce(combine_dict, [t.get(key,{}) for t in tables]) 

    return result


def create_glyps(codes):
    return {code:{ 'glyph': chr(int('0x'+code, 16)) } for code in codes}


def create_char_dict(code, name):
    return {'code': code, 'name': name}


def generate_svgfont(font, svgfilepath):
    font.generate(svgfilepath)
    return svgfilepath
    

def get_code(glyph):
    return glyph.codepoint[2:].lower()


def get_glyphs(font):
    return [g for g in list(font.glyphs()) if g.codepoint]


def generate_svgs(glyphs, svgdirectory):
    result = {}

    for glyph in glyphs:
        code = get_code(glyph)
        svgfile = svgdirectory + code + '.svg'
        glyph.export(svgfile)
        result[code] = { 'svgfile': svgfile }

    return result


def extract_from_glyph(glyph):
    return {
        'code': get_code(glyph),
        'glyphname': glyph.glyphname,
        'boundingbox': glyph.boundingBox()
    }


def extract_from_glyphs(glyphs):
    result = [extract_from_glyph(g) for g in glyphs]
    return {g['code']:g for g in result}
 

def extract_from_css(cssfilepath):
    with open(cssfilepath, 'r') as f:
        css = f.read()

    names = re.findall(r'nf-(.*):', css)
    codes = re.findall(r'"\\(.*)"', css)

    return {c:create_char_dict(c, n) for (c, n) in zip(codes, names)}


def extract_from_svg(svgfilepath):
    svg = xml.dom.minidom.parse(svgfilepath)
    viewbox = svg.getElementsByTagName('svg')[0].getAttribute('viewBox')
    paths = [p.getAttribute('d') for p in svg.getElementsByTagName('path')]

    return { 'viewbox': viewbox, 'paths': paths }


def extract_from_svgs(svgfiles):
    files = [(code, value['svgfile']) for (code, value) in svgfiles.items()]
    return { code:extract_from_svg(fn) for (code, fn) in files }


def remove_unnamed(combined_data):
    return {key:value for (key, value) in combined_data.items() if value.get('name')}


def create_combined():
    download_resources()

    table = extract_from_css(resources['cssfile']['filepath'])

    font = fontforge.open(resources['fontfile']['filepath'])

    glyph_data = extract_from_glyphs(get_glyphs(font))

    svg_files = generate_svgs(get_glyphs(font), 'svg/')
    svg_file_data = extract_from_svgs(svg_files)

    combined_data = combine_tables(table, glyph_data, svg_files, svg_file_data)
    combined_data = combine_tables(combined_data, create_glyps(combined_data.keys()))
    combined_data = remove_unnamed(combined_data)


save_json('nf.json', create_combined())
