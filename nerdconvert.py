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
            print('Skip download', name, ':', resource['filepath'])
        else:
            os.makedirs(os.path.dirname(resource['filepath']), exist_ok=True)
            print('Downloading', name, ':', resource['url'])
            urllib.request.urlretrieve(resource['url'], resource['filepath'])
            print('Saved', name, ':', resource['filepath'])


def save_file(filepath, content):
    dirname = os.path.dirname(filepath)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def camel(match):
    return match.group(1) + match.group(2).upper()


def to_camel_case(string):
    return re.sub(r'(.*?)[-_](\w)', camel, string)


def combine_dict(a, b):
    return {**a, **b}


def dict_to_js(data):
    json_data = json.dumps(data, ensure_ascii=False)
    return re.sub(r'"([a-zA-Z_]*)":', r'\1:', json_data)


def dict_to_json(data):
    return json.dumps(data, ensure_ascii=False, indent=4)


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
    groups, iconnames = zip(*[n.split('-') for n in names])

    fields = ['code', 'name', 'group', 'iconname']
    field_values = zip(codes, names, groups, iconnames)

    data = [dict(zip(fields, values)) for values in field_values]  
    return {record['code']:record for record in data}


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


modifiers = {
    'camelcase': to_camel_case,
    'upper': lambda x: x.upper(),
    'lower': lambda x: x.lower(),
}


class FieldFormatter:
    def __init__(self, field_description, rename=True):
        field = field_description.split(':')
        self.name = field[0]
        if rename:
            self.new_name = field[1] if len(field) > 1 else field[0]
            self.modifiers = [modifiers[m] for m in field[2:] if m in modifiers]
        else:
            self.new_name = field[0]
            self.modifiers = [modifiers[m] for m in field[1:] if m in modifiers]
    
    def apply_modifiers(self, value):
        for m in self.modifiers:
            value = m(value)
        return value
    
    def format(self, record):
        value = record.get(self.name, None)
        return (self.new_name, self.apply_modifiers(value)) if value else None
    

class FilenameFormatter:
    def __init__(self, filename):
        self.format_string = re.sub(r'\{(\w+)[a-zA-Z:]*\}', r'{\1}', filename)
        field_descriptions = re.findall(r'\{([a-zA-Z:]+)\}', filename)
        self.field_formatters = [FieldFormatter(fd, False) for fd in field_descriptions]

    def format(self, record):
        formatted_fields = [f.format(record) for f in self.field_formatters] 
        replacements = {f[0]:f[1] for f in formatted_fields if f}
        return self.format_string.format(**replacements)


class RecordFormatter:
    def __init__(self, field_descriptions):
        self.field_formatters = [FieldFormatter(fd, True) for fd in field_descriptions] 

    def format(self, record):
        formatted_fields = [f.format(record) for f in self.field_formatters] 
        return {f[0]:f[1] for f in formatted_fields if f}


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
    print('Extracted iconinfo from cssfile:',
            resources['cssfile']['filepath'])

    glyph_data = extract_from_glyphs(get_glyphs(font))
    print('Extracted iconinfo from fontfile:',
            resources['fontfile']['filepath'])
    
    svgdir = os.path.join(svgdir, '')
    os.makedirs(svgdir, exist_ok=True)
    svg_files = generate_svgs(get_glyphs(font), svgdir)
    print('Generated svgicons from fontfile:',
            resources['fontfile']['filepath'], '=>', svgdir+'*.svg')

    svg_file_data = extract_from_svgs(svg_files)
    print('Extracted inconpaths from svgfiles:', svgdir+'*.svg')


    data = combine_tables(table, glyph_data, svg_files, svg_file_data)
    data = combine_tables(data, create_glyps(data.keys()))
    data = remove_unnamed(data)

    return sorted(list(data.values()), key=lambda r: r['name'])


def split_path(path, extension=None, default_filename=None):
    if extension and default_filename and not path.endswith(extension):
        path = os.path.join(path, default_filename+extension)

    dirname, filename = os.path.split(path)
    while r'{' in dirname:
        dirname, fn = os.path.split(dirname)
        filename = os.path.join(fn, filename)
    return (dirname, filename)
        

def export_csv(filepath, data, record_formatter):
    import csv
    base_dir, file_name = split_path(filepath, '.csv', 'nerdfonts')
    fieldnames = [ff.new_name for ff in record_formatter.field_formatters]
    export_data = [record_formatter(record) for record in data]

    with open(os.path.join(base_dir, file_name), 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(export_data)

    return data


def export_json(filepath, data, record_formatter):
    base_dir, file_name = split_path(filepath, '.json', 'nerdfonts')
    export_data = [record_formatter.format(record) for record in data]
    print(os.path.join(base_dir, file_name))
    save_file(os.path.join(base_dir, file_name), dict_to_json(export_data))

    return data


def export_svg(filepath, data, record_formatter):
    import shutil
    base_dir, file_name = split_path(filepath, '.svg', '{code}_{name}')
    
    filename_formatter = FilenameFormatter(os.path.join(base_dir, file_name))

    for record in data:
        filename = filename_formatter.format(record)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        shutil.copy(record['svgfile'], filename)
        record['svgfile'] = filename

    return data

def export_es_single(filepath, record, record_formatter):
    filtered_record = record_formatter.format(record)
    content = 'export default ' + dict_to_js(filtered_record) 
    save_file(filepath, content)
    return (filepath, record)


def export_es_index_single(base_dir, module_filepath, name, record):
    import_path = os.path.relpath(module_filepath, start=base_dir)
    import_path = os.path.join('.', import_path)
    index_path = os.path.join(base_dir, 'index.js')

    content = '/* '+record['glyph']+' */ export { default as '+name+' } '
    content += 'from \''+ import_path.replace('.js', '') +'\';\n'

    with open(index_path, 'a', encoding='utf-8') as f:
        f.write(content)
    
def export_es(filepath, data, record_formatter):
    base_dir, file_name = split_path(filepath, '.js', '{name}')

    filename_formatter = FilenameFormatter(
            os.path.join(base_dir, '{group}/{iconname}.js'))

    files = []

    for record in data:
        file_path = filename_formatter.format(record)
        files.append(export_es_single(file_path, record, record_formatter))

    for (file_path, record) in files:
        main_module_name = to_camel_case(record['name'])
        export_es_index_single(base_dir, file_path, main_module_name, record)
        
        group_module_name = to_camel_case(record['iconname'])
        if re.match(r'^[^a-z]', group_module_name):
            group_module_name = main_module_name
        group_base_dir = os.path.dirname(file_path)
        export_es_index_single(group_base_dir, file_path, group_module_name, record)
        
    return data

        
def parse_args():

    fields = ['code', 'name', 'glyphname', 'iconname', 'group',
                'glyph', 'svgfile', 'viewbox', 'paths']

    parser = argparse.ArgumentParser(
        description='Convert nerd-font-icons to SVG / JSON / CSV / ESModule',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--download', default='/tmp/nerdfonts_dl/', type=str,
        help='Download Directory for nerd-fonts resources (ttf/css)')

    
    parser.add_argument('--fields', default=fields, type=str, nargs='*',
        metavar='',
        help='One or more fields that will be included in the '
        'output file.\n A field can be specified in the form of'
        'FIELDNAME[:REPLACEMENT[:MODIFIER]]\n' 
        'e.g. name:iconname:camelcase will include the "name"-field,\n'
        'rename it to "iconname" and convert the fieldvalues to camelcase.\n'
        'Possible FIELDNAMEs are '+', '.join(fields))

    parser.add_argument('--filter', nargs=2, type=str,
        metavar=('FIELD', 'REGEX'), action='append',
        help='Filter FIELD by REGEX (can be used multiple times)')

    
    parser.add_argument('-o', '--output',
        type=str, nargs='+', action='append',
        metavar=('FORMAT', 'FILEPATH'), help='Output')

    return parser.parse_args()


def main():

    args = parse_args()

    base_url = 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master'

    resources = {
        'fontfile': {
            'url': base_url+'/src/glyphs/Symbols-2048-em%20Nerd%20Font%20Complete.ttf',
            'filepath': os.path.join(args.download,
                'Symbols-2048-em_Nerd_Font_Complete.ttf')
            },
        'cssfile': {
            'url': base_url+'/css/nerd-fonts-generated.css',
            'filepath': os.path.join(args.download, 'nerd-fonts-generated.css')
            }
        }


    raw_data = create_raw_data(resources, False, '/tmp/nerdfonts_svg/')

    data = filter_records(raw_data, args.filter) if args.filter else raw_data
    
    record_formatter = RecordFormatter(args.fields)
    
    exporters = {
            'json': export_json,
            'csv': export_csv,
            'svg': export_svg,
            'es': export_es
            }

    for output in args.output:
        exporter = exporters.get(output[0], None)
        if exporter:
            print('running exporter', output[0])
            exporter(output[1], data, record_formatter)
        else:
            print(f'exporter for format"{output[0]}"does not exist')

    
    #save_json(args.json, data)

    print('done!')


if __name__ == '__main__':
    main()
