#!/bin/bash


mkdir -p nerdfonts

curl 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/src/glyphs/Symbols-2048-em%20Nerd%20Font%20Complete.ttf' \
    -o nerdfonts/Symbols-2048-em_Nerd_Font_Complete.ttf

curl 'https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/css/nerd-fonts-generated.css' \
    -o nerdfonts/nerd-fonts-generated.css


mkdir -p svg

fontforge -quiet -lang=ff -c 'Open($1); SelectWorthOutputting(); foreach Export("svg/%u.svg"); endloop;' nerdfonts/Symbols-2048-em_Nerd_Font_Complete.ttf 

echo 'created svg/*.svg'

tmp_glyphs="$(mktemp)"

awk '
    BEGIN {
        OFS = "; ";
        print "codepoint", "glyph", "name";
    }

    /^.nf-/ {
        match($0, /^.nf-(.*):/, n);
    }

    /\scontent:/ {
        match($0, /\\(.*)"/, c);
        print c[1], "\\u"c[1], n[1];
    }
' nerdfonts/nerd-fonts-generated.css > "$tmp_glyphs"


sed -i -E 's/[-_](.)/\U\1/g' "$tmp_glyphs"

echo -e "$(<"$tmp_glyphs")" > "$tmp_glyphs"

tmp_paths="$(mktemp)"

awk '
    BEGIN {
        OFS = "; "
        print "codepoint", "viewbox", "d";
    }

    /viewBox/ {
        match($0, /viewBox="(.*)"/, vb)
    }

    /d=/,/\/>/ {
        out = out" "$0;
    }

    /\/>/ {
        if(match(out, /d="(.*)"/, d)){
            match(FILENAME, /svg\/(.*).svg/, fn);
            print fn[1], vb[1], d[1];
        }
        out = ""
    }
' svg/*.svg > "$tmp_paths"


tmp_glyphs_json="$(mktemp)"
tmp_paths_json="$(mktemp)"

jq --raw-input --slurp '[split("\n") | .[1:-1][] | split("; ") | {(.[0]): {glyph: .[1], name: .[2]} }] | add' "$tmp_glyphs" > "$tmp_glyphs_json"

jq --raw-input --slurp '[split("\n") | .[1:-1][] | split("; ") | {(.[0]): {viewbox: .[1], d: .[2]} }] | add' "$tmp_paths" > "$tmp_paths_json"

jq --slurp '[ .[0] * .[1] | to_entries | .[] | select(.value.name != null) | .value.codepoint = .key | .value]' "$tmp_paths_json" "$tmp_glyphs_json" > nerdfonts_svg.json
echo "created nerdfonts_svg.json"

jq -r '(map(keys) | add | unique) as $cols | map(. as $row | $cols | map($row[.])) as $rows | $cols, $rows[] | @csv' nerdfonts_svg.json > nerdfonts_svg.csv
echo "created nerdfonts_svg.csv"

mkdir -p 'icons'

jq -c '.[]' nerdfonts_svg.json | awk '
    BEGIN {
        print "" > "icons/index.js";
    }
    {
        match($0, /"name":"([^"]*)"/, n);
        filename = n[1]".js";
        print "export default", $0 > "icons/" filename;
        print "export { default as", n[1], "} from \"./" filename "\";" >> "icons/index.js";
    }
'


