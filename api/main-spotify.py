#! /usr/bin/env python

import argparse
import ConfigParser
import os

import spotify as sp


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=True,
                        help="a Spotify Username")

    return parser.parse_args()


def main():
    args = parse_args()

    # load your config.ini file
    parent_dir = os.path.dirname(os.path.dirname(__file__))
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
    track_urls = sp.get_playlist_track_urls(playlists, args.username)

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


if __name__ == "__main__":
    main()
