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


class Processor:
    """
    Processor base class
    """

    name = None
    parent = None
    supported = None
    enabled = True

    def __init__(self, name=None, parent=None, supported=None, **kwargs):
        self.name = name
        self.parent = parent
        self.supported = supported if supported else lambda parent: True

    @property
    def info(self):
        return self.name

    def process(self, content, debug=False, **kwargs):
        return content

    def __repr__(self):
        return f"Processor <{self.__class__.__name__} {self.info}>"

    def __str__(self):
        return repr(self)

    # def __unicode__(self):
    #     return unicode(repr(self))


class ReProcessor(Processor):
    """
    Regex processor
    """

    pattern = None
    replace_with = None

    def __init__(
        self, pattern, replace_with, name=None, supported=None, entry=False, **kwargs
    ):
        super(ReProcessor, self).__init__(name=name, supported=supported)
        self.pattern = pattern
        self.replace_with = replace_with
        self.use_entry = entry

    def process(self, content, debug=False, entry=None, **kwargs):
        if not self.use_entry:
            return self.pattern.sub(self.replace_with, content)

        ret = self.pattern.sub(self.replace_with, entry)
        if not ret:
            raise EmptyEntryError
        elif ret != entry:
            return ret
        return content


class NReProcessor(ReProcessor):
    pass


class MultipleWordReProcessor(ReProcessor):
    """
    Expects a dictionary in the form of:
    dict = {
        "data": {"old_value": "new_value"},
        "pattern": compiled re object that matches data.keys()
    }
    replaces found key in pattern with the corresponding value in data
    """

    def __init__(self, snr_dict, name=None, parent=None, supported=None, **kwargs):
        super(ReProcessor, self).__init__(name=name, supported=supported)
        self.snr_dict = snr_dict

    def process(self, content, debug=False, **kwargs):
        if not self.snr_dict["data"]:
            return content

        return self.snr_dict["pattern"].sub(
            lambda x: self.snr_dict["data"][x.group(0)], content
        )


class EmptyEntryError(Exception):
    pass


class SubtitleModification:
    identifier = None
    description = None
    long_description = None
    exclusive = False
    advanced = False  # has parameters
    args_mergeable = False
    order = None
    modifies_whole_file = False  # operates on the whole file, not individual entries
    apply_last = False
    only_uppercase = False
    pre_processors = []
    processors = []
    post_processors = []
    last_processors = []
    languages = []

    def __init__(self):
        return

    def _process(
        self, content, processors, debug=False, parent=None, index=None, **kwargs
    ):
        if not content:
            return

        # processors may be a list or a callable
        # if callable(processors):
        #    _processors = processors()
        # else:
        #    _processors = processors
        _processors = processors

        new_content = content
        for processor in _processors:
            if not processor.supported(parent):
                if debug and processor.enabled:
                    # logger.debug("Processor not supported, skipping: %s", processor.name)
                    processor.enabled = False
                continue

            old_content = new_content
            new_content = processor.process(new_content, debug=debug, **kwargs)
            if not new_content:
                # if debug:
                #     logger.debug("Processor returned empty line: %s", processor.name)
                break
            if debug:
                if old_content == new_content:
                    continue
                # logger.debug("%d: %s: %s -> %s", index, processor.name, repr(old_content), repr(new_content))

        return new_content

    def pre_process(self, content, debug=False, parent=None, **kwargs):
        return self._process(
            content, self.pre_processors, debug=debug, parent=parent, **kwargs
        )

    def process(self, content, debug=False, parent=None, **kwargs):
        return self._process(
            content, self.processors, debug=debug, parent=parent, **kwargs
        )

    def post_process(self, content, debug=False, parent=None, **kwargs):
        return self._process(
            content, self.post_processors, debug=debug, parent=parent, **kwargs
        )

    def modify(self, content, debug=False, parent=None, procs=None, **kwargs):
        if not content:
            return

        new_content = content
        for method in procs or ("pre_process", "process", "post_process"):
            if not new_content:
                return
            new_content = self._process(
                new_content,
                getattr(self, f"{method}ors"),
                debug=debug,
                parent=parent,
                **kwargs,
            )

        return new_content

    @classmethod
    def get_signature(cls, **kwargs):
        string_args = ",".join([
            f"{key}={value}" for key, value in kwargs.items()
        ])
        return f"{cls.identifier}({string_args})"

    @classmethod
    def merge_args(cls, args1, args2):
        raise NotImplementedError


class SubtitleTextModification(SubtitleModification):
    pass


class StringProcessor(Processor):
    """
    String replacement processor base
    """

    def __init__(
        self, search, replace, name=None, parent=None, supported=None, **kwargs
    ):
        super(StringProcessor, self).__init__(name=name, supported=supported)
        self.search = search
        self.replace = replace

    def process(self, content, debug=False, **kwargs):
        return content.replace(self.search, self.replace)


class MultipleLineProcessor(Processor):
    """
    replaces stuff in whole lines

    takes a search/replace dict as first argument
    Expects a dictionary in the form of:
    dict = {
        "data": {"old_value": "new_value"}
    }
    """

    def __init__(self, snr_dict, name=None, parent=None, supported=None, **kwargs):
        super(MultipleLineProcessor, self).__init__(name=name, supported=supported)
        self.snr_dict = snr_dict

    def process(self, content, debug=False, **kwargs):
        if not self.snr_dict["data"]:
            return content

        for key, value in self.snr_dict["data"].items():
            # if debug and key in content:
            #     logger.debug(u"Replacing '%s' with '%s' in '%s'", key, value, content)

            content = content.replace(key, value)

        return content


class WholeLineProcessor(MultipleLineProcessor):
    def process(self, content, debug=False, **kwargs):
        if not self.snr_dict["data"]:
            return content
        content = content.strip()

        for key, value in self.snr_dict["data"].items():
            if content == key:
                # if debug:
                #     logger.debug(u"Replacing '%s' with '%s'", key, value)

                content = value
                break

        return content


class MultipleWordProcessor(MultipleLineProcessor):
    """
    replaces words
    takes a search/replace dict as first argument
    Expects a dictionary in the form of:
    dict = {
        "data": {"old_value": "new_value"}
    }
    """

    def process(self, content, debug=False, **kwargs):
        words = content.split(" ")
        new_words = []
        for word in words:
            new_words.append(self.snr_dict.get(word, word))

        return " ".join(new_words)
