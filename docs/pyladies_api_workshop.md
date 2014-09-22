# PyLadies Workshop - Saturday

### Timeline

* 9:30a - folks need extra installation help
* 10:00a - doors open
* 10:30a - breakfast
* 12:30p - lunch
* 4:00p - wrap up


## Introduction
10:30a - 10:45a

* Introduce mentors
* Overview of workshop
	* What the goals are & what we can expect to leave with an understanding of
	* What we can expect to accomplish
	 
#### Goals

Primary:

* Interacting with a few public APIs
* A primer to HTTP "verbs"
* File input & output
* Writing Python modules, classes, methods and functions

Secondary:

* Making a simple graph with `matplotlib`
* Logging
* Command-line arguments with Python
* Configuration parsing
* What JSON is
* What OAuth is

#### What you'll leave with

* Python code that interacts with:
	* Spotify APIs
	* EchoNest APIs
	* GitHub APIs
* Two visualizations
	* Bar graph
	* Map
* Understanding of:
	* How to install Python packages and work with Python virtual environments
	* What an API is
	* How to "chop up data" from an API for your enjoyment
	
#### Intro to APIs

* What is an API
* Quick look at some documentation
* Play with Spotify's API console

	
## Part I: Initial Project setup

10:45a - 11:15a - Setting up a Python project/script to run from the command-line:

* writing the basics of `api.py`:
	* basic `main()` function
	* boilerplate `if __name__ == '__main__'`
	* parse arguments
	* setup logging
	* read & parse a configuration file
	
## Part IIa: Spotify API

11:15a - 12:30p (~lunch) - interacting with the Spotify API

* start with Python interpreter with simple GET requests & JSON parsing
* Writing `spotify.py`:
	* get oauth token
	* get a user's playlists
	* parse out track URLs from a user's playlists
	* save the JSON output of the parsed track URLs
	* sort the track URLs "save date" into date-buckets
	* create a bar chart

## Part IIb: Adding to api.py

After lunch (1:15ish):

* importing `spotify` into `api.py` & run
	* add config parsing
	* add logging statements

## Part III: EchoNest API

1:30p - 2:30p - interacting with the EchoNest API

* start with Python interpreter with simple GET requests & JSON parsing
* Writing `echonest.py`:
	* creating an `EchoNestArtist` class
	* adding a method to get coordinates of the `EchoNestArtist` class
	* de-duplicate and load artist information created from `spotify.py`
	* get artist information & create an EchoNestArtist instance for each artist
	* save artist info as a JSON file
* import `echonest` into `api.py` and run
	* add config parsing
	* add logging statements

## Part IV: GitHub API

2:30p - 3:30p - interacting with the GitHub API

* Writing `github.py`:
	* load artist JSON file created from `echonest.py`
	* create a GeoJSON file from the artist JSON file
	* sign into GitHub 
	* post the GeoJSON to GitHub to create a Gist
	* open the web browser to the Gist URL 
* import `github` into `api.py` and run
	* add config parsing
	* add logging statements
	
## Bonus

If we have time:

* Writing a `__main__.py` module to run scripts, e.g. `spotify --user=foo` rather than `python spotify.py --user=foo`
* Explore what else Spotify & EchoNest has to offer
	* Other data we can get
	* Other possible graphs we can make
	