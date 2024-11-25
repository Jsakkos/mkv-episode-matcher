# MIT License
#
# Copyright (c) 2018 Hannes Tismer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Copyright for portions of project Sub-Zero are held by Bram Walet, 2014 as part of project Subliminal.bundle.
# The original license is supplied below.
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Bram Walet
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import re

from Libraries.SubZero.dictionaries.data import data
from Libraries.SubZero.SubZero import (
    MultipleLineProcessor,
    MultipleWordReProcessor,
    NReProcessor,
    ReProcessor,
    SubtitleTextModification,
    WholeLineProcessor,
)
from tld import get_tld


class CommonFixes(SubtitleTextModification):
    identifier = "common"
    description = "Basic common fixes"
    exclusive = True
    order = 40

    long_description = "Fix common and whitespace/punctuation issues in subtitles"

    processors = [
        # normalize hyphens
        NReProcessor(re.compile(r"(?u)([‑‐﹘﹣])"), "-", name="CM_hyphens"),
        # -- = em dash
        NReProcessor(
            re.compile(r"(?u)(\w|\b|\s|^)(-\s?-{1,2})"), r"\1—", name="CM_multidash"
        ),
        # line = _/-/\s
        NReProcessor(
            re.compile(r'(?u)(^\W*[-_.:<>~"\']+\W*$)'), "", name="CM_non_word_only"
        ),
        # remove >>
        NReProcessor(re.compile(r"(?u)^\s?>>\s*"), "", name="CM_leading_crocodiles"),
        # line = : text
        NReProcessor(
            re.compile(r"(?u)(^\W*:\s*(?=\w+))"), "", name="CM_empty_colon_start"
        ),
        # fix music symbols
        NReProcessor(
            re.compile(r"(?u)(^[-\s>~]*[*#¶]+\s+)|(\s*[*#¶]+\s*$)"),
            lambda x: "♪ " if x.group(1) else " ♪",
            name="CM_music_symbols",
        ),
        # '' = "
        NReProcessor(
            re.compile(r"(?u)([\'’ʼ❜‘‛][\'’ʼ❜‘‛]+)"), '"', name="CM_double_apostrophe"
        ),
        # double quotes instead of single quotes inside words
        NReProcessor(
            re.compile(r'(?u)([A-zÀ-ž])"([A-zÀ-ž])'),
            r"\1'\2",
            name="CM_double_as_single",
        ),
        # normalize quotes
        NReProcessor(
            re.compile(r'(?u)(\s*["”“‟„])\s*(["”“‟„]["”“‟„\s]*)'),
            lambda match: '"' + (" " if match.group(2).endswith(" ") else ""),
            name="CM_normalize_quotes",
        ),
        # normalize single quotes
        NReProcessor(re.compile(r"(?u)([\'’ʼ❜‘‛])"), "'", name="CM_normalize_squotes"),
        # remove leading ...
        NReProcessor(re.compile(r"(?u)^\.\.\.[\s]*"), "", name="CM_leading_ellipsis"),
        # remove "downloaded from" tags
        NReProcessor(re.compile(r"(?ui).+downloaded\s+from.+"), "", name="CM_crap"),
        # no space after ellipsis
        NReProcessor(
            re.compile(r'(?u)\.\.\.(?![\s.,!?\'"])(?!$)'),
            "... ",
            name="CM_ellipsis_no_space",
        ),
        # no space before spaced ellipsis
        NReProcessor(
            re.compile(r"(?u)(?<=[^\s])(?<!\s)\. \. \."),
            " . . .",
            name="CM_ellipsis_no_space2",
        ),
        # multiple spaces
        NReProcessor(re.compile(r"(?u)[\s]{2,}"), " ", name="CM_multiple_spaces"),
        # more than 3 dots
        NReProcessor(re.compile(r"(?u)\.{3,}"), "...", name="CM_dots"),
        # no space after starting dash
        NReProcessor(re.compile(r"(?u)^-(?![\s-])"), "- ", name="CM_dash_space"),
        # remove starting spaced dots (not matching ellipses)
        NReProcessor(
            re.compile(r"(?u)^(?!\s?(\.\s\.\s\.)|(\s?\.{3}))(?=\.+\s+)[\s.]*"),
            "",
            name="CM_starting_spacedots",
        ),
        # space missing before doublequote
        ReProcessor(
            re.compile(r'(?u)(?<!^)(?<![\s(\["])("[^"]+")'),
            r" \1",
            name="CM_space_before_dblquote",
        ),
        # space missing after doublequote
        ReProcessor(
            re.compile(r'(?u)("[^"\s][^"]+")([^\s.,!?)\]]+)'),
            r"\1 \2",
            name="CM_space_after_dblquote",
        ),
        # space before ending doublequote?
        # replace uppercase I with lowercase L in words
        NReProcessor(
            re.compile(r"(?u)([a-zà-ž]+)(I+)"),
            lambda match: r"{}{}".format(match.group(1), "l" * len(match.group(2))),
            name="CM_uppercase_i_in_word",
        ),
        # fix spaces in numbers (allows for punctuation: ,.:' (comma/dot only fixed if after space, those may be
        # countdowns otherwise); don't break up ellipses
        NReProcessor(
            re.compile(
                r"(?u)(\b[0-9]+[0-9:\']*(?<!\.\.)\s+(?!\.\.)[0-9,.:\'\s]*(?=[0-9]+)[0-9,.:\'])"
            ),
            lambda match: match.group(1).replace(" ", "")
            if match.group(1).count(" ") == 1
            else match.group(1),
            name="CM_spaces_in_numbers",
        ),
        # uppercase after dot
        # NReProcessor(re.compile(r'(?u)((?<!(?=\s*[A-ZÀ-Ž-_0-9.]\s*))(?:[^.\s])+\.\s+)([a-zà-ž])'),
        #              lambda match: r'%s%s' % (match.group(1), match.group(2).upper()), name="CM_uppercase_after_dot"),
        # remove double interpunction
        NReProcessor(
            re.compile(r"(?u)(\s*[,!?])\s*([,.!?][,.!?\s]*)"),
            lambda match: match.group(1).strip()
            + (" " if match.group(2).endswith(" ") else ""),
            name="CM_double_interpunct",
        ),
        # remove spaces before punctuation; don't break spaced ellipses
        NReProcessor(
            re.compile(r"(?u)(?:(?<=^)|(?<=\w)) +([!?.,](?![!?.,]| \.))"),
            r"\1",
            name="CM_punctuation_space",
        ),
        # add space after punctuation
        NReProcessor(
            re.compile(r"(?u)(([^\s]*)([!?.,:])([A-zÀ-ž]{2,}))"),
            lambda match: f"{match.group(2)}{match.group(3)} {match.group(4)}"
            if not get_tld(match.group(1), fail_silently=True, fix_protocol=True)
            else match.group(1),
            name="CM_punctuation_space2",
        ),
        # fix lowercase I in english
        NReProcessor(
            re.compile(r"(?u)(\b)i(\b)"),
            r"\1I\2",
            name="CM_EN_lowercase_i",
            # supported=lambda p: p.language == ENGLISH),
        ),
    ]


class FixOCR(SubtitleTextModification):
    identifier = "OCR_fixes"
    description = "Fix common OCR issues"
    exclusive = True
    order = 10
    data_dict = None

    long_description = "Fix issues that happen when a subtitle gets converted from bitmap to text through OCR"

    def __init__(self, language):
        super(FixOCR, self).__init__()
        data_dict = data.get(language)
        if not data_dict:
            # logger.debug("No SnR-data available for language %s", parent.language)
            return

        self.data_dict = data_dict
        self.processors = self.get_processors()

    def get_processors(self):
        if not self.data_dict:
            return []

        return [
            # remove broken HI tag colons (ANNOUNCER'., ". instead of :) after at least 3 uppercase chars
            # don't modify stuff inside quotes
            NReProcessor(
                re.compile(
                    r'(?u)(^[^"\'’ʼ❜‘‛”“‟„]*(?<=[A-ZÀ-Ž]{3})[A-ZÀ-Ž-_\s0-9]+)'
                    r'(["\'’ʼ❜‘‛”“‟„]*[.,‚،⹁、;]+)(\s*)(?!["\'’ʼ❜‘‛”“‟„])'
                ),
                r"\1:\3",
                name="OCR_fix_HI_colons",
            ),
            # fix F'bla
            NReProcessor(
                re.compile(r"(?u)(\bF)(\')([A-zÀ-ž]*\b)"), r"\1\3", name="OCR_fix_F"
            ),
            WholeLineProcessor(self.data_dict["WholeLines"], name="OCR_replace_line"),
            MultipleWordReProcessor(
                self.data_dict["WholeWords"], name="OCR_replace_word"
            ),
            MultipleWordReProcessor(
                self.data_dict["BeginLines"], name="OCR_replace_beginline"
            ),
            MultipleWordReProcessor(
                self.data_dict["EndLines"], name="OCR_replace_endline"
            ),
            MultipleWordReProcessor(
                self.data_dict["PartialLines"], name="OCR_replace_partialline"
            ),
            MultipleLineProcessor(
                self.data_dict["PartialWordsAlways"],
                name="OCR_replace_partialwordsalways",
            ),
        ]
