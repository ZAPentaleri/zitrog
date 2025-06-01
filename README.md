
# Zoe's ID3 Tag Retroencoder for Outdated Gadgets &mdash; ZITROG

## Introduction
A Q&D utility for re-encoding modern MP3 ID3 tags into obsolete encoding formats
for use with outdated gadgets -- MP3 players, PDAs, localized PC media players,
etc. At present, only Unicode decoding and Shift-JIS encoding are supported, but
other formats may be added in the future.

## Usage
`id3_retroencode [-h] [-a ACTION] [-i INPUT [INPUT ...]] [-o OUTPUT] [-p PRESERVE [PRESERVE ...]] [-u] [-w] [-v]`

## Arguments
```
  -h, --help            show this help message and exit
  -a ACTION, --action ACTION
                        Tag processing action
                        Supported actions: retroencode
  -i INPUT [INPUT ...], --input INPUT [INPUT ...]
                        Input file path (accepts multiple, wildcards)
  -o OUTPUT, --output OUTPUT
                        Output directory
  -p PRESERVE [PRESERVE ...], --preserve PRESERVE [PRESERVE ...]
                        Tags to preserve. Tags which are not explicitly
                        preserved, or which do not occur in the input file, will
                        not be encoded in the output file.
                        Defaults to: TALB TPE1 TPE2 TCOP TPOS TCON TIT2 TRCK TYER
  -u, --automatic       Automatically accept suggested tag changes for character
                        restrictions in output encoding
  -w, --overwrite       Overwrite existing files on output without prompt
  -v, --verbose         Enable verbose output during encoding
```

## Demonstration
![An example of a retro device displaying re-encoded ID3 tags](https://github.com/ZAPentaleri/zitrog/blob/main/saisei.png?raw=true)  
*Welcome back, PEG-NZ90.*

## Artwork
```
    _______ ______     __
    \___  // ||   \   / /
       / //  || |\ | / /
      / // / || |/ |/ /
     / //_/| ||  _//_/
    /_____\|_||_| /_/ (R)

```
