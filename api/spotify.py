#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

import argparse
import base64
import ConfigParser
import datetime
import logging
import json
import os
from operator import itemgetter

# note - need to download X11.app
import matplotlib.pyplot as plt
import numpy as np
import requests


class SpotifyApiError(Exception):
    pass


# Get OAuth token
def get_spotify_oauth_token(client_id, client_secret, token_url):
    to_encode = client_id + ":" + client_secret
    bearer_token = base64.b64encode(to_encode)
    headers = {"Authorization": "Basic {t}".format(t=bearer_token)}
    data = {'grant_type': 'client_credentials'}
    response = requests.post(url=token_url,
                             headers=headers,
                             data=data)

    if response.status_code == requests.codes.ok:
        return response.json()['access_token']
    else:
        response_error = json.loads(response.text).get('error')
        msg = "Error getting OAuth token: {e}".format(e=response_error)
        raise SpotifyApiError(msg)


# get playlists
def get_user_playlists(token, username):
    headers = {"Authorization": "Bearer {t}".format(t=token)}
    playlist_url = "https://api.spotify.com/v1/users/{0}/playlists".format(
        username)
    response = requests.get(url=playlist_url, headers=headers)

    if response.status_code == requests.codes.ok:
        return response.json()
    else:
        response_error = json.loads(response.text).get('error')
        msg = "Error getting {0}'s playlists: {1}".format(username,
                                                          response_error)
        raise SpotifyApiError(msg)


# get tracks of playlists
def get_playlist_track_urls(playlists):
    track_urls = []
    items = playlists.get('items')
    for item in items:
        tracks = item.get('tracks')
        tracks_url = tracks.get('href')
        track_urls.append(tracks_url)
    return track_urls


def get_tracks(track_urls, token):
    headers = {"Authorization": "Bearer {t}".format(t=token)}
    track_data = []
    for url in track_urls:
        response = requests.get(url=url, headers=headers)
        if response.status_code == requests.codes.ok:
            items = response.json().get('items')
            track_data.append(items)
    return track_data


def parse_raw_date(raw_date):
    # 2014-09-09T15:00:27Z
    if raw_date:
        year = int(raw_date[:4])
        month = int(raw_date[5:7])
        day = int(raw_date[8:10])
        return datetime.date(year, month, day)
    return datetime.date(2000, 01, 01)


def parse_track_data(track_data):
    parsed_track_data = []
    json_data = []
    for playlist in track_data:
        for track in playlist:
            ttrack = track.get('track')
            if ttrack:
                name = ttrack.get('name')
                added_at_raw = track.get('added_at')
                added_at = parse_raw_date(added_at_raw)
                parsed_track_data.append((name, added_at))

                artists = ttrack.get('artists')
                added_at_str = parse_raw_date(added_at_raw).strftime("%Y-%m")
                artist_names = [n.get('name') for n in artists]
                json_data.append((name, added_at_str, artist_names))
            else:
                continue

    parsed_track_data = sorted(parsed_track_data, key=itemgetter(1))
    return parsed_track_data, json_data


def save_json_data(json_data, output_file):
    with open(output_file, 'w') as f:
        json.dump(json_data, f)


def create_buckets(beg_date, end_date):
    buckets = [beg_date]

    bucket = beg_date
    while bucket < end_date:
        year, month = divmod(bucket.month + 1, 12)
        if month == 0:
            month = 12
            year = year - 1
        bucket = datetime.date(bucket.year + year, month, 1)
        buckets.append(bucket)

    return buckets


def sort_track_data(track_data):
    # returns {'2011-01': 5, '2011-02': 0, '2011-03': 4}
    cumulated_data = {}
    beginning_date = track_data[0][1]
    ending_date = track_data[-1][1]

    buckets = create_buckets(beginning_date, ending_date)

    for b in buckets:
        bucket = b.strftime("%Y-%m")
        counter = 0
        for t in track_data:
            if t[1].year == b.year and t[1].month == b.month:
                counter += 1
        cumulated_data[bucket] = counter

    return cumulated_data


def create_bar_chart(track_data):

    labels = track_data.keys()
    values = track_data.values()

    width = 0.3
    ind = np.arange(len(values))
    fig = plt.figure(figsize=(len(labels) * 1.8, 10))

    # Generate a subplot and put our values onto it.
    ax = fig.add_subplot(1, 1, 1)
    ax.bar(ind, values, width, align='center')

    plt.ylabel("Number of songs added")
    plt.xlabel("Month Buckets")
    ax.set_xticks(ind + 0.3)
    ax.set_xticklabels(labels)
    fig.autofmt_xdate()
    plt.grid(True)

    plt.savefig("Music Timeline", dpi=72)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--spotify-user', required=True,
                        help="Spotify User ID")
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help="Increases the output level.")

    return parser.parse_args()


def main():
    args = parse_args()

    log = logging.getLogger('spotify_api')
    stream = logging.StreamHandler()
    log.addHandler(stream)

    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")

    config = ConfigParser.ConfigParser()
    config.read(config_file)

    spotify_client_id = config.get('spotify', 'client_id')
    spotify_client_secret = config.get('spotify', 'client_secret')
    spotify_token_url = config.get('spotify', 'token_url')

    log.debug("Getting a Spotify OAuth Token with your client ID")
    token = get_spotify_oauth_token(spotify_client_id,
                                    spotify_client_secret,
                                    spotify_token_url)

    log.debug("Getting public playlists for {0}".format(args.spotify_user))
    playlists = get_user_playlists(token, args.spotify_user)

    log.debug("Parsing out track URLs from each playlist")
    track_urls = get_playlist_track_urls(playlists)
    log.debug("Parsed tracks from {0} playlists.".format(len(track_urls)))

    log.debug("Fetching track data for each track URL.")
    track_data = get_tracks(track_urls, token)
    log.debug("Received track data on {0} playlists.".format(len(track_data)))

    log.debug("Parsing track data, and creating & saving a JSON file.")
    parsed_data, json_data = parse_track_data(track_data)

    output_file_name = config.get('spotify', 'output_file_name')
    output_file = os.path.abspath(os.path.realpath(output_file_name))
    save_json_data(json_data, output_file)
    log.debug("Saved the JSON file at: '{0}'".format(output_file))

    log.debug("Sorting parsed track data.")
    sorted_data = sort_track_data(parsed_data)

    log.debug("Attempting to create an awesome bar chart...")
    create_bar_chart(sorted_data)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    log.debug("Chart saved as 'Music Timeline.png' in '{0}'.".format(
              current_dir))
    log.debug("Finished!")


if __name__ == '__main__':
    main()
