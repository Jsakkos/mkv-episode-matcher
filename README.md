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
This way, the API key and show directory file path are not saved in a file that could be accessible to others. Keep in mind, however, that these values can still appear in system logs or in process lists, so it's essential to limit access to these resources as much as possible.

## Technical Requirements
The MKV Episode Matcher requires the following packages: python-tmdb, requests, pytest, coveralls, and unittest. To install these dependencies, simply call `pip install -r requirements.txt` from your command line and it will automatically download all required packages. This tool also requires an internet connection to download episode images and rename episodes based on their content.

## Environment Variables
This tool uses environment variables for configuration. The following variables are required:

TMDB_API_KEY - The TMDb API key.
SHOW_DIR - The main directory that contains all of the episodes for a specific show.
These variables can be provided in one of two ways:

By directly inputting them into your terminal like so:
```
TMDB_API_KEY=`your-api-key` SHOW_DIR='/path/to/show' python main.py --tmdb-api-key $TMDB_API_KEY --show-dir $SHOW_DIR
```
By providing a file path to your .env file containing these variables:
In this case, the .env file should look like the following:

## Input Key
TMDB_API_KEY= `your-api-key`
SHOW_DIR = '/path/to/show'
In this example, the .env file is used to provide environment variables when calling the script. To do this, simply call python main.py --env /path/to/.env from your command line and it will automatically use these variables. However, keep in mind that using a .env file can still pose some security risks if not managed properly, so only share these files with trusted individuals or limit access as much as possible.