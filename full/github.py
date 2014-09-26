#! /usr/bin/env python

import github3
import geojson


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

    d = {"type": "FeatureCollection", "features": geo_list}

    geojson_output = geojson.dumps(d)

    return geojson_output


def login_github(github_oauth):
    try:
        return github3.login(token=github_oauth)
    except github3.GitHubError as e:
        msg = "Issue logging into GitHub: {0}".format(e)
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
        raise GithubError(msg)

    gist_url = gist.html_url

    return gist_url
