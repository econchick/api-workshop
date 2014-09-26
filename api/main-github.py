#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

# standard library packages/modules
import argparse
import ConfigParser
import json
import os
import webbrowser

import pyen

import echonest as ec
import github as gh
import spotify as sp


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True,
                        help="a Spotify Username")
    parser.add_argument('-g', '--gist-desc', default="Location of Artists",
                        help="Description for your GitHub Gist")

    return parser.parse_args()


def main():
    args = parse_args()

    # load your config.ini file
    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    # parse out spotify configuration
    spotify_client_id = config.get('spotify', 'client_id')
    spotify_client_secret = config.get('spotify', 'client_secret')
    spotify_token_url = config.get('spotify', 'token_url')

    # Get an OAuth token from Spotify
    token = sp.get_spotify_oauth_token(spotify_client_id,
                                       spotify_client_secret,
                                       spotify_token_url)

    # get the desired user's list of playlists
    playlists = sp.get_user_playlists(token, args.username)

    # parse out the tracks URL for each playlist
    track_urls = sp.get_playlist_track_urls(playlists)

    # request track data from the tracks URLs
    track_data = sp.get_tracks(track_urls, token)

    # parse track data into parsed_data and json_data
    parsed_data, json_data = sp.parse_track_data(track_data)

    # save the json_data for future use with EchoNest
    output_file_name = config.get('spotify', 'output_file_name')
    output_file = os.path.abspath(os.path.realpath(output_file_name))
    sp.save_json_data(json_data, output_file)

    # sort the parsed_data of tracks into their appropriate buckets
    sorted_data = sp.sort_track_data(parsed_data)

    # create a bar chart with the sorted_data!
    sp.create_bar_chart(sorted_data)

    # EchoNest API

    # Grab your EchoNest API key from your config
    echonest_api_key = config.get('echonest', 'api_key')

    # Grab where you saved the track data from Spotify
    output_file_name = config.get('echonest', 'output_file_name')
    json_input = config.get('spotify', 'output_file_name')

    # instantiate the EchoNest APY
    en = pyen.Pyen(echonest_api_key)

    # Open the track data we saved from Spotify
    playlist_json = json.load(open(json_input, "r"))

    # Deduplicate the artists
    unique_artists = ec.deduplicate_artists(playlist_json)

    # Get our artist information
    artists = ec.get_artists_information(en, unique_artists)

    # Create a JSON-like object with our artist information
    json_output = ec.create_json(artists)

    # Define where the JSON will be saved based off of our config
    output_file = os.path.abspath(os.path.realpath(output_file_name))

    # Save the data into a JSON file
    ec.save_json(json_output, output_file)

    # GitHub API

    # Load GitHub configuration
    github_oauth = config.get('github', 'oauth')

    # Grab the file that we saved with echonest earlier
    artist_data_file = config.get('echonest', 'output_file_name')

    # load this file so we can read it
    artist_json = json.load(open(artist_data_file, 'r'))

    # Create a GeoJSON-like object with our artist information
    geojson_output = gh.create_geojson(artist_json)

    # Either log into GitHub if you do have a GitHub account
    if github_oauth:
        try:
            gh_auth = gh.login_github(github_oauth)
        except gh.GithubError:
            gh_auth = None

    # Or if no account, then set the auth to None
    else:
        gh_auth = None

    # POST the GeoJSON to GitHub
    gist_url = gh.post_gist_github(geojson_output, gh_auth, args.gist_desc)

    # Open the default system browser to the gist URL that we just created
    webbrowser.open(gist_url)

if __name__ == '__main__':
    main()
