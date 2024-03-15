# MKV Episode Matcher
 
The MKV Episode Matcher is a tool for identifying TV series episodes from MKV files and renaming the files accordingly. To use the MKV Episode Matcher, follow these steps:

1. Obtain an API key from TMDb (https://developers.themoviedb.org/authentication/getting-a-apikey).
1. Provide a filepath to your show directory. This is the main directory that contains all of the episodes for a specific show.
1. Call `python __main__.py` with the TMDB_API_KEY and SHOW_DIR as arguments or in environment variables from your command line:
```
python main.py --tmdb-api-key `your-api-key` --show-dir /path/to/show
```

The MKV Episode Matcher will download episode images and rename episodes based on their content.
You can pass the api key and show directory as CLI arguments when calling the script instead of including them in a .env file:
python main.py --tmdb-api-key `your-api-key` --show-dir /path/to/show


