#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

import argparse
import ConfigParser
import json
import logging
import os
import webbrowser

import github3
import geojson


log = logging.getLogger('github_api')
stream = logging.StreamHandler()
log.addHandler(stream)


class GithubError(Exception):
    pass


def create_geojson(artists):
    geo_list = []
    j = 1
    for artist in artists:
        if artist.get('coordinates') == [0, 0]:
            continue

        data = {}
        data["type"] = "Feature"
        data["id"] = j
        data["properties"] = {
            "title": artist.get('name'),
            "spotify_id": artist.get('spotify_id'),
            "genres": ", ".join(artist.get('genres')),
            "location": artist.get('location').get('location'),
            "marker-symbol": 'music'
        }
        data["geometry"] = geojson.Point(artist.get('coordinates'))
        j += 1
        geo_list.append(data)

    d = {"type": "FeatureCollection"}
    for item in geo_list:
        d.setdefault("features", []).append(item)

    return geojson.dumps(d)


def login_github(github_oauth):
    try:
        return github3.login(token=github_oauth)
    except github3.GitHubError as e:
        msg = "Issue logging into GitHub: {0}".format(e)
        log.error(msg)
        raise GithubError(msg)


def post_gist_github(geojson, auth, title):
    files = {
        'artists.geojson': {
            'content': geojson
        }
    }

    try:
        if not auth:
            gist = github3.create_gist(title, files)
        else:
            gist = auth.create_gist(title, files, public=False)
    except github3.GitHubError as e:
        msg = "Issue posting an anonymous Gist: {0}".format(e)
        log.error(msg)
        raise GithubError(msg)

    return gist.html_url


def parse_args():
    parser = argparse.ArgumentParser()
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

    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    artist_data_file = config.get('echonest', 'output_file_name')
    #artist_data_file = 'test_gist.json'
    artist_json = json.load(open(artist_data_file, 'r'))

    log.debug("Creating a GeoJSON file with artist info from {0}".format(
              artist_data_file))
    geojson_file = create_geojson(artist_json)

    github_oauth = config.get('github', 'oauth')
    if github_oauth:
        log.debug("Logging you into GitHub...")
        try:
            gh = login_github(github_oauth)
            log.debug("Successfully logged into GitHub! \n"
                      "Posting the gist to your Account.")
        except GithubError:
            gh = None
            log.info("Could not log you in. Will post your Gist anonymously.")
    else:
        gh = None

    gist_url = post_gist_github(geojson_file, gh, args.gist_desc)

    log.info("Your gist has been posted! Navigating you to: {0}".format(
             gist_url))
    webbrowser.open(gist_url)


if __name__ == "__main__":
    main()
