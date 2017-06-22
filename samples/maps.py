from __future__ import division
from math import pi, exp, atan, log, tan
import sys
import os
import json
import threading
from ast import literal_eval
from collections import OrderedDict
from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Effect
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication

# Handle external dependencies for this sample
try:
    import mapbox_vector_tile
    import requests
    from google.protobuf.message import DecodeError
except ImportError:
    print("Run `pip install mapbox-vector-tile protobuf requests` to fix your dependencies.")
    sys.exit(0)


class Map(Effect):
    # Replace this value with the free one that you get from signing up with www.mapbox.com
    _KEY = ""
    _URL = "http://a.tiles.mapbox.com/v4/mapbox.mapbox-streets-v7/{}/{}/{}.mvt?access_token={}"
    _START_SIZE = 64
    _ZOOM_IN_SIZE = _START_SIZE * 2
    _ZOOM_OUT_SIZE = _START_SIZE // 2
    _ZOOM_STEP = exp(log(2) / 6)

    def __init__(self, screen):
        super(Map, self).__init__()
        # Current state of the map
        self._screen = screen
        self._zoom = 0
        self._latitude = 51.4778
        self._longitude = -0.0015
        self._tiles = OrderedDict()
        self._size = self._START_SIZE

        # Desired viewing location and animation flags
        self._desired_zoom = self._zoom
        self._desired_latitude = self._latitude
        self._desired_longitude = self._longitude
        self._next_update = 100000

        # Start the thread to read in the tiles
        self._updated = threading.Event()
        self._updated.set()
        self._oops = None
        self._thread = threading.Thread(target=self._get_tiles)
        self._thread.daemon = True
        self._thread.start()

    def _scale_coords(self, x, y, extent, xo, yo):
        # Convert from tile coordinates to "pixels" - i.e. text characters.
        return xo + (x * self._size * 2 / extent), yo + ((extent - y) * self._size / extent)

    def _convert_longitude(self, longitude):
        # Convert from longitude to the x position in overall map.
        return int((180 + longitude) * (2 ** self._zoom) * self._size / 360)

    def _convert_latitude(self, latitude):
        # Convert from latitude to the y position in overall map.
        return int((180 - (180 / pi * log(tan(
                pi / 4 + latitude * pi / 360)))) * (2 ** self._zoom) * self._size / 360)

    def _get_tiles(self):
        # Background thread to download tiles as required.
        while True:
            self._updated.wait()
            self._updated.clear()

            # Save off current view and find the nearest tile.
            zoom = self._zoom
            size = self._size
            n = 2 ** zoom
            x_offset = self._convert_longitude(self._longitude)
            x_centre = int(x_offset // size)
            y_offset = self._convert_latitude(self._latitude)
            y_centre = int(y_offset // size)

            # Get the visible tiles around that location - getting most relevant first
            for x, y, z in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0),
                            (0, 0, -1), (0, 0, 1),
                            (1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)]:
                # Don't get tile if it falls off the grid
                x_tile = x_centre + x
                y_tile = y_centre + y
                z_tile = zoom + z
                if (x_tile < 0 or x_tile >= n or y_tile < 0 or y_tile >= n or
                        z_tile < 0 or z_tile > 20):
                    continue

                # Don't bother rendering if the tile is not visible
                top = y_tile * size - y_offset + self._screen.height // 2
                left = (x_tile * size - x_offset + self._screen.width // 4) * 2
                if (left > self._screen.width or left + self._size * 2 < 0 or
                        top > self._screen.height or top + self._size < 0):
                    continue

                # Check for in memory or file cache before downloading.
                try:
                    cache_file = "mapscache/{}.{}.{}.json".format(z_tile, x_tile, y_tile)
                    if cache_file not in self._tiles:
                        if os.path.isfile(cache_file):
                            with open(cache_file, 'rb') as f:
                                tile = json.load(f)
                        else:
                            url = self._URL.format(z_tile, x_tile, y_tile, self._KEY)
                            data = requests.get(url).content
                            try:
                                tile = mapbox_vector_tile.decode(data)
                                with open(cache_file, 'wb') as f:
                                    json.dump(literal_eval(repr(tile)), f)
                            except DecodeError:
                                tile = None
                        if tile:
                            self._tiles[cache_file] = [x_tile, y_tile, z_tile, tile]
                            if len(self._tiles) > 80:
                                self._tiles.popitem(False)
                            self._screen.force_update()
                except Exception as e:
                    self._oops = "{} {} {} {} {}".format(e, x_tile, y_tile, x, y)

            # Generally refresh screen after we've downloaded everything
            self._screen.force_update()

    def _get_features(self):
        # Decide which layers to render based on current zoom level.
        if self._zoom <= 2:
            return [
                ("water", [], [], 153),
                ("marine_label", [], [1], 12),
            ]
        elif self._zoom <= 7:
            return [
                ("admin", [], [], 7),
                ("water", [], [], 153),
                ("road", ["motorway"], [], 15),
                ("country_label", [], [], 9),
                ("marine_label", [], [1], 12),
                ("state_label", [], [], 1),
                ("place_label", [], ["city", "town"], 0),
            ]
        elif self._zoom <= 10:
            return [
                ("admin", [], [], 7),
                ("water", [], [], 153),
                ("road", ["motorway", "motorway_link", "trunk"], [], 15),
                ("country_label", [], [], 9),
                ("marine_label", [], [1], 12),
                ("state_label", [], [], 1),
                ("place_label", [], ["city", "town"], 0),
            ]
        else:
            return [
                ("landuse", ["agriculture", "grass", "park"], [], 193),
                ("water", [], [], 153),
                ("waterway", ["river", "canal"], [], 153),
                ("building", [], [], 252),
                ("road",
                 ["motorway", "motorway_link", "trunk", "primary"] if self._zoom <= 14 else
                 ["motorway", "motorway_link", "trunk", "primary", "secondary", "tertiary",
                  "link", "street", "tunnel"],
                 [], 15),
                ("poi_label", [], [], 8),
            ]

    def _draw_feature(self, feature, extent, colour, bg, xo, yo):
        # Draw a single feature from a layer in a map tile.
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            coords = []
            for polygon in geometry["coordinates"]:
                coords.append([self._scale_coords(x, y, extent, xo, yo) for x, y in polygon])
                self._screen.fill_polygon(coords, colour=colour, bg=bg)
        elif feature["geometry"]["type"] == "MultiPolygon":
            for multi_polygon in geometry["coordinates"]:
                coords = []
                for polygon in multi_polygon:
                    coords.append([self._scale_coords(x, y, extent, xo, yo) for x, y in polygon])
                self._screen.fill_polygon(coords, colour=colour, bg=bg)
        elif feature["geometry"]["type"] == "LineString":
            coords = [self._scale_coords(x, y, extent, xo, yo) for x, y in geometry["coordinates"]]
            for i, (x, y) in enumerate(coords):
                if i == 0:
                    self._screen.move(x, y)
                else:
                    self._screen.draw(x, y, colour=colour, bg=bg, thin=True)
        elif feature["geometry"]["type"] == "MultiLineString":
            for line in geometry["coordinates"]:
                coords = [self._scale_coords(x, y, extent, xo, yo) for x, y in line]
                for i, (x, y) in enumerate(coords):
                    if i == 0:
                        self._screen.move(x, y)
                    else:
                        self._screen.draw(x, y, colour=colour, bg=bg, thin=True)
        elif feature["geometry"]["type"] == "Point":
            x, y = self._scale_coords(
                    geometry["coordinates"][0], geometry["coordinates"][1], extent, xo, yo)
            text = u" {} ".format(feature["properties"]["name_en"])
            self._screen.print_at(text, int(x - len(text) / 2), int(y), colour=colour, bg=bg)

    def _update(self, frame_no):
        # Check for any fatal errors from the background thread and quit if we hit anything.
        if self._oops:
            raise RuntimeError(self._oops)

        # Glide towards desired location
        self._next_update = 100000
        if self._zoom != self._desired_zoom:
            self._next_update = 1
            if self._desired_zoom < self._zoom:
                self._size /= self._ZOOM_STEP
                if self._size <= self._ZOOM_OUT_SIZE:
                    if self._zoom > 0:
                        self._zoom -= 1
                        self._size *= 2
                        self._updated.set()
                    else:
                        self._size = self._ZOOM_OUT_SIZE
                        self._next_update = 100000
            else:
                self._size *= self._ZOOM_STEP
                if self._size >= self._ZOOM_IN_SIZE:
                    if self._zoom < 20:
                        self._zoom += 1
                        self._size /= 2
                        self._updated.set()
                    else:
                        self._size = self._ZOOM_IN_SIZE

        if self._longitude != self._desired_longitude:
            self._next_update = 1
            self._updated.set()
            if self._desired_longitude < self._longitude:
                self._longitude = max(self._longitude - 360 / 2 ** self._zoom / self._size * 2,
                                      self._desired_longitude)
            else:
                self._longitude = min(self._longitude + 360 / 2 ** self._zoom / self._size * 2,
                                      self._desired_longitude)

        if self._latitude != self._desired_latitude:
            self._next_update = 1
            self._updated.set()
            if self._desired_latitude < self._latitude:
                self._latitude = max(self._inc_lat(self._latitude, 2), self._desired_latitude)
            else:
                self._latitude = min(self._inc_lat(self._latitude, -2), self._desired_latitude)

        # Re-draw the tiles - if we have any suitable ones downloaded.
        count = 0
        x_offset = self._convert_longitude(self._longitude)
        y_offset = self._convert_latitude(self._latitude)
        if self._tiles:
            # Clear the area first.
            bg = 253 if self._screen.unicode_aware else 0
            for y in range(self._screen.height):
                self._screen.print_at("." * self._screen.width, 0, y, colour=bg, bg=bg)

            # Render all visible tiles a layer at a time.
            for layer_name, c_filters, t_filters, colour in self._get_features():
                try:
                    for x, y, z, tile in self._tiles.values():
                        # Convert tile location into pixels
                        x *= self._size
                        y *= self._size

                        # Don't bother rendering if the tile is not visible
                        left = (x - x_offset + self._screen.width // 4) * 2
                        top = y - y_offset + self._screen.height // 2
                        if (left > self._screen.width or left + self._size * 2 < 0 or
                                top > self._screen.height or top + self._size < 0 or
                                z != self._zoom):
                            continue

                        # Now we can draw the visible geometry in the map tile.
                        count += 1
                        _layer = tile[layer_name]
                        _extent = float(_layer["extent"])
                        for _feature in _layer["features"]:
                            if c_filters and _feature["properties"]["class"] not in c_filters:
                                continue
                            if (t_filters and _feature["type"] not in t_filters and
                                    _feature["properties"]["type"] not in t_filters):
                                continue

                            self._draw_feature(
                                    _feature, _extent, colour, bg,
                                    (x - x_offset + self._screen.width // 4) * 2,
                                    y - y_offset + self._screen.height // 2)
                except KeyError:
                    pass

        # Just a few pointers on what the user should do...
        if count == 0:
            self._screen.centre(" Loading - please wait... ", self._screen.height // 2, 1)

        self._screen.centre("Use cursor keys and '+'/'-' to navigate around.", 0, 1)
        if self._KEY == "":
            footer = "Using local cached data - go to https://www.mapbox.com/ and get a free key."
        else:
            footer = "Zoom: {} Location: {}, {}".format(self._zoom, self._longitude, self._latitude)
        self._screen.centre(footer, self._screen.height - 1, 1)

        # We're ready to go - flush it all to screen.
        self._screen.refresh()

    def _inc_lat(self, latitude, delta):
        # Shift the latitude by the required number of pixels (i.e. text lines).
        y = self._convert_latitude(latitude)
        y += delta
        return 360 / pi * atan(
                exp((180 - y * 360 / (2 ** self._zoom) / self._size) * pi / 180)) - 90

    def process_event(self, event):
        # Key handling for the demo.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code == ord("+") and self._zoom <= 20:
                if self._desired_zoom < 20 and self._KEY != "":
                    self._desired_zoom += 1
            elif event.key_code == ord("-") and self._zoom >= 0:
                if self._desired_zoom > 0 and self._KEY != "":
                    self._desired_zoom -= 1
            elif event.key_code == ord("0"):
                self._desired_zoom = 0
            elif event.key_code == ord("9"):
                self._desired_zoom = 20
            elif event.key_code == Screen.KEY_LEFT:
                self._desired_longitude -= 360 / 2 ** self._zoom / self._size * 10
            elif event.key_code == Screen.KEY_RIGHT:
                self._desired_longitude += 360 / 2 ** self._zoom / self._size * 10
            elif event.key_code == Screen.KEY_UP:
                self._desired_latitude = self._inc_lat(self._desired_latitude, -self._size / 10)
            elif event.key_code == Screen.KEY_DOWN:
                self._desired_latitude = self._inc_lat(self._desired_latitude, self._size / 10)
            else:
                return

            # Trigger a reload of the tiles and redraw map
            self._updated.set()
            self._screen.force_update()

    @property
    def frame_update_count(self):
        # Only redraw if required - as determined by the update logic.
        return self._next_update

    @property
    def stop_frame(self):
        # No specific end point for this Effect.  Carry on running forever.
        return 0

    def reset(self):
        # Nothing special to do.  Just need this to satisfy the ABC.
        pass


def demo(screen):
    screen.play([Scene([Map(screen)], -1)], stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
