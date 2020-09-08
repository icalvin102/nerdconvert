import os
import re
import urllib.request
import json
import fontforge
import argparse
import xml.dom.minidom 
from functools import reduce


def download_resources(resources, force=False):
    for (name, resource) in resources.items():
        if os.path.isfile(resource['filepath']) and not force:
            print('File exists. Skip download', name, ':', resource['filepath'])
        else:
            os.makedirs(os.path.dirname(resource['filepath']), exist_ok=True)
            print('Downloading', name, ':', resource['url'])
            urllib.request.urlretrieve(resource['url'], resource['filepath'])
            print('Saved', name, ':', resource['filepath'])


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def camel(match):
    return match.group(1) + match.group(2).upper()


def to_camel_case(string):
    return re.sub(r'(.*?)[-_](\w)', camel, string)

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
      #  'boundingbox': glyph.boundingBox()
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


def remove_unnamed(data):
    return {k:v for (k, v) in data.items() if v.get('name')}


def modify_fields(data, fields):
    modifiers = {
        'camelcase': to_camel_case,
        'upper': lambda x: x.upper(),
        'lower': lambda x: x.lower(),
    }

    split_fields = [f.split(':') for f in fields]
    modified_fields = [f for f in split_fields if len(f) > 1]

    result = []
    for record in data:
        new_record = dict(record)
        for f in modified_fields:
            current = new_record[f[0]]
            for m in f[2:]:
                current = modifiers.get(m, lambda x: x)(current)
            new_record[f[1]] = current
        result.append(new_record)

    return result


def filter_fields(data, fields):
    field_names = [f.split(':') for f in fields]
    field_names = [f[0] if len(f) < 2 else f[1] for f in field_names]
    print(field_names)
    return [{f:record[f] for f in field_names if f in record} for record in data ]

def match_filters(record, filters):
    for f in filters:
        if not re.match(f[1], record[f[0]]):
            return False
    return True

def filter_records(data, filters):
    return [record for record in data if match_filters(record, filters)]

def create_raw_data(resources, force_download=False, svgdir='svg'):
    download_resources(resources, force_download)
    
    font = fontforge.open(resources['fontfile']['filepath'])

    table = extract_from_css(resources['cssfile']['filepath'])
    print('Extracted iconinfo from cssfile:', resources['cssfile']['filepath'])

    glyph_data = extract_from_glyphs(get_glyphs(font))
    print('Extracted iconinfo from fontfile:', resources['fontfile']['filepath'])
    
    svgdir = os.path.join(svgdir, '')
    os.makedirs(svgdir, exist_ok=True)
    svg_files = generate_svgs(get_glyphs(font), svgdir)
    print('Generated svgicons from fontfile:', resources['fontfile']['filepath'], '=>', svgdir+'*.svg')

    svg_file_data = extract_from_svgs(svg_files)
    print('Extracted inconpaths from svgfiles:', svgdir+'*.svg')


    data = combine_tables(table, glyph_data, svg_files, svg_file_data)
    data = combine_tables(data, create_glyps(data.keys()))
    data = remove_unnamed(data)

    return list(data.values())


def export_csv(filepath, data, fieldnames):
    import csv

    with open(filepath, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)


def to_json(data):
    pass


def export_es(data):
    pass 


def parse_args():

    fields = ['code', 'name', 'glyphname', 'glyph', 'svgfile', 'viewbox', 'paths']

    parser = argparse.ArgumentParser(
            description='Convert nerd-font-icons to SVG / JSON / CSV / ESModule',
            formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--download', default='/tmp/nerdfonts_dl/', type=str,
                        help='Download Directory for nerd-fonts resources (ttf/css)')

    parser.add_argument('--svg', default='', type=str, metavar='SVG_FILE',
                        help='Export Directory for the *.svg files')

    parser.add_argument('--json', default='nerd-fonts.json', type=str, metavar='JSON_FILE',
                        help='Filename of the *.json output')

    parser.add_argument('--csv', default='', type=str, metavar='CSV_FILE',
                        help='Filename of the *.csv output')

    parser.add_argument('--es', default='', type=str, metavar='ESMODULE_FILE',
                        help='Filename of the *.js output')

    parser.add_argument('--fields', default=fields, type=str, nargs='*', metavar='FIELDNAME[:REPLACEMENT[:MODIFIER]]',
                        help='One or more fields that will be included in the output file.\n'
                            'A field can be specified in the form of FIELDNAME[:REPLACEMENT[:MODIFIER]]\n'
                            'e.g. name:iconname:camelcase will include the "name"-field,\n'
                            'rename it to "iconname" and convert the fieldvalues to camelcase.\n'
                            'Possible FIELDNAMEs are '+', '.join(fields))

    parser.add_argument('--filter', nargs=2, type=str, metavar=('FIELD', 'REGEX'), action='append',
                        help='Filter FIELD by REGEX (can be used multiple times)')

    return parser.parse_args()


def main():

    args = parse_args()

    resources = {
        'fontfile': {
            'url': 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/src/glyphs/Symbols-2048-em%20Nerd%20Font%20Complete.ttf',
            'filepath': os.path.join(args.download, 'Symbols-2048-em_Nerd_Font_Complete.ttf')
            },
        'cssfile': {
            'url': 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/css/nerd-fonts-generated.css',
            'filepath': os.path.join(args.download, 'nerd-fonts-generated.css')
            }
        }


    raw_data = create_raw_data(resources, False, '/tmp/nerdfonts_svg/')

    data = modify_fields(raw_data, args.fields)
    data = filter_records(data, args.filter)
    data = filter_fields(data, args.fields)
    #data = raw_data
    
    if args.csv:
        export_csv(args.csv, data, args.fields)

    save_json(args.json, data)

    print('done!')


if __name__ == '__main__':
    main()
