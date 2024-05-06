=====================================
MKV Episode Matcher API Documentation
=====================================

CLI
===

.. automodule:: mkv_episode_matcher.__main__
    :members:
    :undoc-members:
    :show-inheritance:

Utils
=====
.. automodule:: mkv_episode_matcher.utils
    :members:
    :undoc-members:
    :show-inheritance:

TMDB Interface
==============
.. automodule:: mkv_episode_matcher.tmdb_client
    :members:
    :undoc-members:
    :show-inheritance:

.. py:function:: get_episode_info(show_name, season, episode)

    Get episode information for a given show, season, and episode number.

    :param str show_name: The name of the show.
    :param int season: The season number.
    :param int episode: The episode number.
    :return: A dictionary containing the episode information.

MKV Conversion
==============
.. automodule:: mkv_episode_matcher.mkv_to_srt
    :members:
    :undoc-members:
    :show-inheritance:

Episode Matching
================
.. automodule:: mkv_episode_matcher.episode_matcher
    :members:
    :undoc-members:
    :show-inheritance:

Configuration
=============
.. automodule:: mkv_episode_matcher.config
    :members:
    :undoc-members:
    :show-inheritance: