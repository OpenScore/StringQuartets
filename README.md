[OpenScore String Quartets][OSSQ]
=================================

[OSSQ]: https://musescore.com/openscore-string-quartets

Mirror of https://musescore.com/openscore-string-quartets.

Collection of string quartets by "long 19th century" composers in MuseScore format with associated data.

Scores can be downloaded individually in PDF, MIDI, MusicXML, MP3 and other formats from
their [official pages][OSSQ] on MuseScore.com. Alternatively, scores can be
converted to other formats *en masse* using MuseScore's free desktop software using either
the [Batch Convert Plugin] 
or the [command line interface][MuseScore Command Line].

# [Scores directory](./scores/)

Score and lyric files are arranged in the following directory structure:

```
<composer>/<set>/
```

Directories:

- `<composer>` - composer's name in the form `Last,_First_Second...`.
- `<set>` - name of the extended work that the song belongs to, if any.

## Filenames

Score files within each song directory are named as follows

```
sq<id>.mscx
```

Filename components:

- `sq` - standing for string quartets
- `<id>` - the score's unique Musescore ID
- `.mscx` - the file extension for MuseScore's uncompressed score format.

## Unicode characters in file paths

With the exception of a few unsafe or illegal characters, names of songs,
sets and composers have been left in their original forms.

Modern filesystems should have no problems with Unicode characters in
file paths. If the paths are displayed incorrectly by `git`, try setting:

```
git config core.quotePath false
```

Users on macOS may also need to set:

```
git config core.precomposeunicode true
```

__Tip:__ Add `--global` after `config` in the above commands to make `git`
behave this way by default for all repositories on your local machine.

# [Data directory](./data/)

The `Data/` directory contains the following:
- composers.tsv and composers.yaml: information about the corpus composers.
- corpus.tsv and corpus.yaml: total numbers of composers, sets, and scores.
- corpus_conversion.json: for batch conversion as described above.
- corpus_conversion.py: a basic script for updating the `corpus_conversion.json` file.
- plot.py: for producing the summative plots contained in ... 
- plots/: a folder for the summative plots as discussed below.
- scores.tsv and scores.yaml: information about each score
- sets.tsv and sets.yaml: information about each set (collection of scores).

## [Data plots](./data/plots/)

Summative plots of the corpus contents:

1. The number of corpus composers alive and active over time.
![composer_dates](./data/code-plots/composer_dates.pdf)

1. The number of works by the top, most represented composers.
![composer_scores](./data/code-plots/composer_scores.pdf)

1. The composer nationalities
![composer_nationalities](./data/code-plots/composer_nationalities.pdf)

# License and acknowledgement

These scores are released under Creative Commons Zero (CC0). See LICENSE.txt.

We kindly ask that you credit OpenScore String Quartets and provide a link to [OSSQ] or this repository for any public-facing use of these scores.

For academic publications, please cite the report on we published in DLfM:

```
TO FOLLOW IN NOV 2023
```
