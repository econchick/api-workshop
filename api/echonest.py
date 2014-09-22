#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2014 Lynn Root

import argparse
import ConfigParser
import datetime
import json
import logging
import os
import time

from geopy.geocoders import Nominatim
import pyen

geolocator = Nominatim()

log = logging.getLogger('echonest_api')
stream = logging.StreamHandler()
log.addHandler(stream)


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
    counter = 0
    skipped = 0
    for artist in artists:
        counter += 1
        log.debug("Fetching info for artist #{0}: {1}".format(counter,
                  artist.encode('UTF-8')))
        try:
            resp = en.get('artist/profile', name=artist,
                          bucket=['artist_location', 'id:spotify',
                                  'genre', 'images'])
            en_artist = EchoNestArtist(resp)
            en_artists.append(en_artist)
        except pyen.PyenException:
            skipped += 1
            log.debug("!!  Issue finding {0}. Continuing on...".format(
                      artist.encode('UTF-8')))

        # NOTE: generally rate limited by EchoNest to 120 calls/minute or
        # 2 calls/second, therefore sleep/wait for .5 seconds in between
        # each call to their API
        time.sleep(.5)

    duplicates = counter - len(en_artists) - skipped
    log.debug("Successfully fetch info for {0} unique artists,"
              " with {1} duplicates, and {2} skipped.".format(len(en_artists),
                                                              duplicates,
                                                              skipped))

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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help="Increases the output level.")

    return parser.parse_args()


def main():
    start = datetime.datetime.now()
    args = parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)

    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")

    config = ConfigParser.ConfigParser()
    config.read(config_file)

    api_key = config.get('echonest', 'api_key')
    en = pyen.Pyen(api_key)

    json_input = config.get('spotify', 'output_file_name')
    playlist_json = json.load(open(json_input, "r"))

    unique_artists = deduplicate_artists(playlist_json)

    log.debug("Fetching artist information for {0} artists.".format(
              len(unique_artists)))
    log.debug("Perhaps go get some coffee, or a have a bathroom break,"
              "this may take a while depending on how many artists "
              "there are :D.")
    artists = get_artists_information(en, unique_artists)

    log.debug("Creating JSON output of artist information.")
    json_output = create_json(artists)

    output_file_name = config.get('echonest', 'output_file_name')
    output_file = os.path.abspath(os.path.realpath(output_file_name))

    log.debug("Saving JSON output to {0}.".format(output_file))
    save_json(json_output, output_file)

    finish = datetime.datetime.now()
    delta = finish - start
    log.debug("Finished in {0} seconds!".format(delta.seconds))


if __name__ == '__main__':
    main()
