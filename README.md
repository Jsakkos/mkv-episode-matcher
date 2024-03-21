# MKV Episode Matcher
 
The MKV Episode Matcher is a tool for identifying TV series episodes from MKV files and renaming the files accordingly. 

## Quick start

To use the MKV Episode Matcher, follow these steps:

1. Clone this repository `git clone https://github.com/Jsakkos/mkv-episode-matcher`
1. Obtain an API key from TMDb (https://developers.themoviedb.org/authentication/getting-a-apikey).
1. Provide a filepath to your show directory. This is the main directory that contains all of the episodes for a specific show.
1. Call `python __main__.py` with the TMDB_API_KEY and SHOW_DIR as arguments or in environment variables from your command line:

```
python __main__.py --api-key `your-api-key` --show-dir /path/to/show
```

## How it works

MKV Episode Matcher compares reference images from TMDb with frames from the mkv content using image hashing. 

## Caveats (WIP)

Currently, MKV Episode Matcher is slow (several minutes per episode), CPU intensive, and error-prone.

# Contributing

Contributions are welcome! If you would like to contribute to the MKV Episode Matcher project, please follow these steps:

1. Fork the repository.
2. Create a new branch for your contribution.
3. Make your changes and commit them to your branch.
4. Push your branch to your forked repository.
5. Open a pull request to the main repository.

Please ensure that your code follows the project's coding conventions and standards. Additionally, provide a clear and detailed description of your changes in the pull request.

Thank you for your contribution!

# License

This project is licensed under the [Creative Commons Attribution-NonCommercial (CC BY-NC) license](https://creativecommons.org/licenses/by-nc/4.0/).

# Acknowledgments
This product uses the TMDB API but is not endorsed or certified by TMDB.
![The Movie DB Logo](https://www.themoviedb.org/assets/2/v4/logos/v2/blue_long_2-9665a76b1ae401a510ec1e0ca40ddcb3b0cfe45f1d51b77a308fea0845885648.svg)
