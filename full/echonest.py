#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

import json
import time

from geopy.geocoders import Nominatim
import pyen

geolocator = Nominatim()


class EchoNestArtist(object):
    def __init__(self, response):
        self.artist = response.get('artist')

    def en_id(self):
        return self.artist.get('id')

    def name(self):
        return self.artist.get('name')

    def location(self):
        return self.artist.get('artist_location')

    def genres(self):
        return [g.get('name') for g in self.artist.get('genres')]

    def images(self):
        return [i.get('url') for i in self.artist.get('images')]

    def spotify_id(self):
        foreign_ids = self.artist.get('foreign_ids')
        for f in foreign_ids:
            if f.get('catalog') == 'spotify':
                return f.get('foreign_id')

    def get_coordinates(self):
        if self.location():
            _location = self.location().get('location')
            _city = self.location().get('city')
            _region = self.location().get('region')
            _country = self.location().get('country')
            if _location:
                location = _location
            elif _city:
                location = _city
                if _region:
                    location = location + ", " + _region
                if _country:
                    location = location + ", " + _country

            if location:
                geo_location = geolocator.geocode(location, exactly_one=True,
                                                  timeout=10)
                try:
                    lat = geo_location.latitude
                    long = geo_location.longitude
                    return long, lat
                except AttributeError:
                    return 0, 0
        return 0, 0


def deduplicate_artists(playlist_json):
    artists = []
    for track in playlist_json:
        for artist in track[2]:
            if artist not in artists:
                artists.append(artist)
    return artists[:50]


def get_artists_information(en, artists):
    en_artists = []
    for artist in artists:
        try:
            resp = en.get('artist/profile', name=artist,
                          bucket=['artist_location', 'id:spotify',
                                  'genre', 'images'])
            en_artist = EchoNestArtist(resp)
            en_artists.append(en_artist)
        except pyen.PyenException:
            pass

        # NOTE: generally rate limited by EchoNest to 120 calls/minute or
        # 2 calls/second, therefore sleep/wait for .5 seconds in between
        # each call to their API
        time.sleep(.5)

    return en_artists


def create_json(artists):
    output_json = []

    for a in artists:
        name = a.name()
        loc = a.location()
        gen = a.genres()
        img = a.images()
        sp = a.spotify_id()
        coords = tuple(a.get_coordinates())

        if coords:
            artist = dict(name=name, location=loc, genres=gen,
                          images=img, spotify=sp, coordinates=coords)
            output_json.append(artist)

    return output_json


def save_json(json_data, output_file):
    with open(output_file, 'w') as f:
        json.dump(json_data, f)
