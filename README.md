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