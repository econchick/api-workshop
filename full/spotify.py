#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

import base64
import datetime
import json
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
    encoded_auth = base64.b64encode(to_encode)
    headers = {"Authorization": "Basic %s" % encoded_auth}
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
    headers = {"Authorization": "Bearer %s" % token}
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
def get_playlist_track_urls(playlists, username):
    track_urls = []
    items = playlists.get('items')
    for item in items:
        if item.get('owner').get('id') != username:
            continue
        else:
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


# NOTE: the more "pythonic" way to do this is:
# >>> import dateutil.parser
# >>> foo = dateutil.parser.parse(raw_date)
# but I'd like to show some string slicing
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
