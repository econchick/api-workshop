#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

# standard library packages/modules
import argparse
import ConfigParser
import json
import logging
import os
import webbrowser

import pyen

import echonest as ec
import github as gh
import spotify as sp

log = logging.getLogger('pyladies_api')
stream = logging.StreamHandler()
log.addHandler(stream)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--spotify-user', required=True,
                        help="Spotify User ID")
    parser.add_argument('-g', '--gist-desc', default="Location of Artists",
                        help="Description for your GitHub Gist")
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help="Increases the output level.")

    return parser.parse_args()


def main():
    args = parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    # Config Shit
    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    echonest_api_key = config.get('echonest', 'api_key')
    spotify_client_id = config.get('spotify', 'client_id')
    spotify_client_secret = config.get('spotify', 'client_secret')
    spotify_token_url = config.get('spotify', 'token_url')
    github_oauth = config.get('github', 'oauth')
    artist_data_file = config.get('echonest', 'output_file_name')
    output_file_name = config.get('echonest', 'output_file_name')
    json_input = config.get('spotify', 'output_file_name')
    artist_json = json.load(open(artist_data_file, 'r'))

    # Spotify API
    log.debug("Getting a Spotify OAuth Token with your client ID")
    token = sp.get_spotify_oauth_token(spotify_client_id,
                                       spotify_client_secret,
                                       spotify_token_url)

    log.debug("Getting public playlists for {0}".format(args.spotify_user))
    playlists = sp.get_user_playlists(token, args.spotify_user)

    log.debug("Parsing out track URLs from each playlist")
    track_urls = sp.get_playlist_track_urls(playlists)
    log.debug("Parsed tracks from {0} playlists.".format(len(track_urls)))

    log.debug("Fetching track data for each track URL.")
    track_data = sp.get_tracks(track_urls, token)
    log.debug("Received track data on {0} playlists.".format(len(track_data)))

    log.debug("Parsing track data, and creating & saving a JSON file.")
    parsed_data, json_data = sp.parse_track_data(track_data)

    output_file_name = config.get('spotify', 'output_file_name')
    output_file = os.path.abspath(os.path.realpath(output_file_name))
    sp.save_json_data(json_data, output_file)
    log.debug("Saved the JSON file at: '{0}'".format(output_file))

    log.debug("Sorting parsed track data.")
    sorted_data = sp.sort_track_data(parsed_data)

    log.debug("Attempting to create an awesome bar chart...")
    sp.create_bar_chart(sorted_data)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    log.debug("Chart saved as 'Music Timeline.png' in '{0}'.".format(
              current_dir))
    log.debug("Finished getting playlists from Spotify!")

    # EchoNest API
    en = pyen.Pyen(echonest_api_key)

    playlist_json = json.load(open(json_input, "r"))

    unique_artists = ec.deduplicate_artists(playlist_json)

    log.debug("Fetching artist information for {0} artists.".format(
              len(unique_artists)))
    log.debug("Perhaps go get some coffee, or a have a bathroom break,"
              "this may take a while depending on how many artists "
              "there are :D.")
    artists = ec.get_artists_information(en, unique_artists)

    log.debug("Creating JSON output of artist information.")
    json_output = ec.create_json(artists)

    output_file = os.path.abspath(os.path.realpath(output_file_name))

    log.debug("Saving JSON output to {0}.".format(output_file))
    ec.save_json(json_output, output_file)

    # GitHub API
    log.debug("Creating a GeoJSON file with artist info from {0}".format(
              artist_data_file))
    geojson_file = gh.create_geojson(artist_json)

    if github_oauth:
        log.debug("Logging you into GitHub...")
        try:
            gh_auth = gh.login_github(github_oauth)
            log.debug("Successfully logged into GitHub! \n"
                      "Posting the gist to your Account.")
        except gh.GithubError:
            gh_auth = None
            log.info("Could not log you in. Will post your Gist anonymously.")
    else:
        gh_auth = None

    gist_url = gh.post_gist_github(geojson_file, gh_auth, args.gist_desc)

    log.info("Your gist has been posted! Navigating you to: {0}".format(
             gist_url))
    webbrowser.open(gist_url)

if __name__ == '__main__':
    main()
