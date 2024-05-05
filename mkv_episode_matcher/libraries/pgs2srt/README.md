# pgs2srt

Uses [pgsreader](https://github.com/EzraBC/pgsreader) and [pyteseract](https://pypi.org/project/pytesseract/) to convert image based pgs subtitles files (.sup) to text based subrip (.srt) files.

## Requirements
Python3, pip3, and Tesseract

## Installation
* Run ```git clone https://github.com/PimvanderLoos/pgs2srt.git```
* Inside the repo folder, run ```pip3 install -r requirements.txt```
* In your .bashrc or .zshrc add ```alias pgs2srt='<absolute path to repo>/pgs2srt.py'```

## How to run

    pgs2srt <pgs filename>.sup

## Improving accuracy
On Debian and Ubuntu, the default trained models files for Tesseract are from the [fast](https://github.com/tesseract-ocr/tessdata_fast) set. While these are a bit faster than other options, this comes at the cost of accuracy. If you want higher accuracy, I'd recommend using either the [legacy](https://github.com/tesseract-ocr/tessdata) or the [best](https://github.com/tesseract-ocr/tessdata_best) trained models. Note that the fast and best options only support the LSTM OCR Engine Mode (oem 1).

## Caveats

This is in no way a perfect converter, and tesseract will make incorrect interpretations of characters. Extremely alpha, issues, pull requests and suggestions welcome!


## Credits
This project uses the common + OCR fixes developed by [Sub-Zero.bundle](https://github.com/pannal/Sub-Zero.bundle).
