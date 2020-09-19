# nerdconvert
Convert nerd-font-icons to SVG / JSON / ESModule / CSV

    
The script will extract `paths`, `viewbox`, `code`, `name`, `glyphname`,
`glyph`, `svgfile` from [nerd-fonts](https://github.com/ryanoasis/nerd-fonts)
iconfont/css and converts it to SVG, JSON, EcmaScript Module and CSV. 

The exported JSON, ESModule directory and CSV file respectivly contain
all the data needed to dynamically create `<svg>`-Tags with JavaScript.


## Usage

If all the [dependencies](#dependencies) are installed you can simply run:

`python nerdconvert.py --output json nerdfonts.json`

This will create a `nerdfonts.json` file in the current directory.

The file contains an array of objects with all the extracted [fields](#fields).

``` js
// nerdfonts.json
[
    // ...
    {
        "code": "26a1",
        "name": "oct-zap",
        "glyphname": "zap",
        "glyph": "⚡",
        "svgfile": "/tmp/nerdfonts_svg/26a1.svg",
        "viewbox": "-10 0 1300 2048",
        "paths": [
            "M1280 827l-1152 1152l384 -896h-512l1152 -1152l-384 896h512z"
        ]
    },
    // ...
]
```

### Output options


The output option `--output FORMAT FILEPATH` or `-o FORMAT FILEPATH`
can be used multiple times and specify a export target.

`FORMAT` can be set to `json`, `es`, `csv` or `svg`

`FILEPATH` specifies a file or directory.
If no fileextension (`.json | .csv | .svg`) a directory is assumed
and a default filename is used.

For formats that generate one file per icon (`svg`)
placeholders in the form of `{FIELD[:MODIFIER[:...]]}` can be used
to create meaningful filenames.
> (See [fields](#fields) and [modifiers](#modifiers) for more details)

***Example***

`python -o svg svgfiles/{name:camelcase}_{code}.svg`

Will create files like `octZap_26a1.svg` in a directory called `svgfiles`


### Fields

The `--fields FIELD[:REPLACEMENT[:MODIFIER]]` option specifies one or more
fields included in the output. If not specified all fields are included.

`FIELD` one of the following field names:

* `paths` *string[]* of svg paths 
* `viewbox` *string* svg viewBox
* `code` *string* unicode codepoint
* `name` *string* name extracted from nerdfont-icons css classnames
* `glyphname` *string* iconname extracted from the font file
* `glyph` *string* actual unicode character 
* `svgfile` *string* filepath to the corresponding `*.svg`-file


`REPLACEMENT` new fieldname the field sould be exported as.

`MODIFIER` modifies the field value. Can be set to:

* `camelcase` make value camelcase
* `upper` make value uppercase
* `lower` make value lowercase

***Exmaple***

```python nerdconvert.py --fields name name:icon:camelcase glyph:unicodechar \
        --output json nerdfont_icons.json
```

Will create:

``` js
// nerdfont_icons.json 
[
    // ...
    { "name": "oct-zap", "icon": "octZap", "unicodechar": "⚡" },
    // ...
]
```



### Filter 

The `--filter FIELD REGEX` option specifies filters to narrow down the 
the exported record. The record will only be exported if the `REGEX`
(regular expression) matches the `FIELD`-value.

> (See [fields](#fields) and
> [python regular expressions](https://docs.python.org/3/library/re.html)
> for more details)

***Example***

```python nerdconvert.py --filter name '^mdi' --filter \
        --output json material_icons.json
```

Will create `material_icons.json` that contains only the Material Design Icons.


### Show Help

`python nerdconvert.py -h`


## Dependencies

To run `nerdconvert.py`, `python` and  `fontforge` need to be installed first.

If not already installed the packages should be availible in
all the major packetmanagers.


**Install dependencies on Arch**

Run: `sudo pacman -S python fontforge`

**Install dependencies on Debian/Ubuntu**

Run: `sudo apt-get install python fontforge`

