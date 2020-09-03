# nerdfonts2jsonsvg
Convert nerd-font-icons to SVG / JSON-SVG / CSV

The script will download `Symbols-2048-em Nerd Font Complete.ttf` from the
[nerd-fonts Project](https://github.com/ryanoasis/nerd-fonts) converts it to
SVG, JSON and CSV. 

The exported JSON and CSV files respectivly contain all the data needed 
to dynamically create `<svg>`-Tags with JavaScript.

**Structure of `.json` file**

``` json
[
    // ...
    {
      "viewbox": "-10 0 1300 2048",
      "d": "M1280 827l-1152 1152l384 -896h-512l1152 -1152l-384 896h512z",
      "glyph": "⚡",
      "name": "oct-zap",
      "codepoint": "26a1"
    },
    // ...
]
```

## Usage

If all the dependencies are installed you can simply run:

`bash <(curl -s 'https://raw.githubusercontent.com/icalvin102/nerdfonts2jsonsvg/master/nf2json.sh')`


Alternativly you can download the
[nf2json.sh](https://raw.githubusercontent.com/icalvin102/nerdfonts2jsonsvg/master/nf2json.sh)
script and run it locally:

`bash nf2json.sh`


This will create `nerdfonts_svg.json`, `nerdfonts_svg.csv` and a `svg/` directory with all
the icons seperated into their own files. The downloaded files from
[nerd-fonts Project](https://github.com/ryanoasis/nerd-fonts) will be in `nerdfons/`.


### Dependencies

To run `nf2json.sh` the packages `curl`, `awk`, `jq` and  `fontforge` need to be installed first.

If not already installed the packages should be availible in all the major packetmanagers.


**Install dependencies on Arch**

Run: `sudo pacman -S curl gawk jq fontforge`

**Install dependencies on Debian/Ubuntu**

Run: `sudo apt-get install curl gawk jq fontforge`





