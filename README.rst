===================
MKV Episode Matcher
===================

|docs|  |pypi|

The MKV Episode Matcher is a tool for identifying TV series episodes from MKV files and renaming the files accordingly.

Quick start
===========

To use the MKV Episode Matcher, follow these steps:

1. Install ``pip install mkv-episode-matcher``
2. Obtain an API key from TMDb (https://developers.themoviedb.org/authentication/getting-a-apikey).
3. (Optional) - Obtain an API key from Opensubtitles.com by creating an API consumer (https://www.opensubtitles.com/en/consumers)
4. Alternatively, add the .srt files to the cache directory. On Windows: ``C:\Users\YOUR_USER_NAME\.mkv-episode-matcher\cache\data\SHOW_NAME``. The files need to be named with the season and episode, e.g. ``Show Name - S01E01.srt``.
5. Provide a filepath to your show directory. This is the main directory that contains all of the episodes for a specific show.

The directory and subfolders must be arranged in the following structure:

- Show name
  - Season 1
  - Season 2
  - ...
  - Season n
  
6. Call ``mkv-match`` with the TMDB_API_KEY and SHOW_DIR as arguments or in environment variables from your command line:

.. code-block:: bash

   python __main__.py --tmdb-api-key `your-api-key` --show-dir /path/to/show

How it works
============

MKV Episode Matcher extracts the subtitle text from each MKV file, then crossreferences the text against .srt subtitle files that are either user-provided or downloaded from Opensubtitles.com

Contributing
============

Contributions are welcome! If you would like to contribute to the MKV Episode Matcher project, please follow these steps:

1. Fork the repository.
2. Clone the repository.
3. Create a new branch for your contribution.
4. Make your changes and commit them to your branch.
5. Push your branch to your forked repository.
6. Open a pull request to the main repository.

Please ensure that your code follows the project's coding conventions and standards. Additionally, provide a clear and detailed description of your changes in the pull request.

Thank you for your contribution!

License
=======

MIT License

Copyright (c) 2024 Jonathan Sakkos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Acknowledgments
===============

This product uses the TMDB API but is not endorsed or certified by TMDB.
.. image:: https://www.themoviedb.org/assets/2/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg
   :alt: The Movie DB Logo

.. |docs| image:: https://readthedocs.org/projects/mkv-episode-matcher/badge/?version=latest
        :target: https://mkv-episode-matcher.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. |pypi| image:: https://badge.fury.io/py/mkv-episode-matcher.svg
        :target: https://badge.fury.io/py/mkv-episode-matcher