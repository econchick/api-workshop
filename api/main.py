#! /usr/bin/env python

import argparse
import ConfigParser
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', required=True,
                        nargs="*", help="Your Name")

    return parser.parse_args()


def main():
    args = parse_args()
    name = " ".join(args.name)

    print "Hello, %s!" % name

    parent_dir = os.path.abspath(os.pardir)
    config_file = os.path.join(parent_dir, "config.ini")
    config = ConfigParser.ConfigParser()
    config.read(config_file)

    color = config.get('pyladies', 'fav_color')
    artist = config.get('pyladies', 'fav_artist')
    food = config.get('pyladies', 'fav_food')

    print "Your favorite color is: %s." % color
    print "Your favorite artist is: %s." % artist
    print "Your favorite food is: %s." % food


if __name__ == "__main__":
    main()
