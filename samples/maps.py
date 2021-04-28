#!/usr/bin/env python3

# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
import traceback
from math import pi, exp, atan, log, tan, sqrt
import sys
import os
import json
import threading
from ast import literal_eval
from collections import OrderedDict
from asciimatics.event import KeyboardEvent
from asciimatics.renderers import ColourImageFile
from asciimatics.effects import Effect
from asciimatics.widgets import Button, Text, Layout, Frame, Divider, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication, InvalidFields
try:
    import mapbox_vector_tile
    import requests
    from google.protobuf.message import DecodeError
except ImportError:
    print("Run `pip install mapbox-vector-tile protobuf requests` to fix your dependencies.")
    print("See https://github.com/Toblerity/Shapely#installing-shapely-16b2 for Shapely install.")
    sys.exit(0)

# Global constants for the applications
# Replace `_KEY` with the free one that you get from signing up with www.mapbox.com
_KEY = ""
_VECTOR_URL = \
    "http://a.tiles.mapbox.com/v4/mapbox.mapbox-streets-v7/{}/{}/{}.mvt?access_token={}"
_IMAGE_URL = \
    "https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/256/{}/{}/{}?access_token={}"
_START_SIZE = 64
_ZOOM_IN_SIZE = _START_SIZE * 2
_ZOOM_OUT_SIZE = _START_SIZE // 2
_ZOOM_ANIMATION_STEPS = 6
_ZOOM_STEP = exp(log(2) / _ZOOM_ANIMATION_STEPS)
_CACHE_SIZE = 180
_HELP = """
You can moved around using the cursor keys.  To jump to any location in the world, press Enter and \
then fill in the longitude and latitude of the location and press 'OK'.

To zoom in and out use '+'/'-'.  To zoom all the way in/out, press '9'/'0'.

To swap between satellite and vector views, press 'T'.  To quit, press 'Q'.
"""


class EnterLocation(Frame):
    """Form to enter a new desired location to display on the map."""
    def __init__(self, screen, longitude, latitude, on_ok):
        super(EnterLocation, self).__init__(
            screen, 7, 40, data={"long": str(longitude), "lat": str(latitude)}, name="loc",
            title="Enter New Location", is_modal=True)
        self._on_ok = on_ok
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Divider(draw_line=False), 1)
        layout.add_widget(Text(label="Longitude:", name="long", validator=r"^[-]?\d+?\.\d+?$"), 1)
        layout.add_widget(Text(label="Latitude:", name="lat", validator=r"^[-]?\d+?\.\d+?$"), 1)
        layout.add_widget(Divider(draw_line=False), 1)
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 1)
        layout2.add_widget(Button("Cancel", self._cancel), 2)
        self.fix()

    def _ok(self):
        try:
            self.save(validate=True)
        except InvalidFields:
            return
        self._on_ok(self)
        self._scene.remove_effect(self)

    def _cancel(self):
        self._scene.remove_effect(self)


class Map(Effect):
    """Effect to display a satellite image or vector map of the world."""

    # Colour palettes
    _256_PALETTE = {
        "landuse": 193,
        "water": 153,
        "waterway": 153,
        "marine_label": 12,
        "admin": 7,
        "country_label": 9,
        "state_label": 1,
        "place_label": 0,
        "building": 252,
        "road": 15,
        "poi_label": 8
    }
    _16_PALETTE = {
        "landuse": Screen.COLOUR_GREEN,
        "water": Screen.COLOUR_BLUE,
        "waterway": Screen.COLOUR_BLUE,
        "marine_label": Screen.COLOUR_BLUE,
        "admin": Screen.COLOUR_WHITE,
        "country_label": Screen.COLOUR_RED,
        "state_label": Screen.COLOUR_RED,
        "place_label": Screen.COLOUR_YELLOW,
        "building": Screen.COLOUR_WHITE,
        "road": Screen.COLOUR_WHITE,
        "poi_label": Screen.COLOUR_RED
    }

    def __init__(self, screen):
        super(Map, self).__init__(screen)
        # Current state of the map
        self._screen = screen
        self._zoom = 0
        self._latitude = 51.4778
        self._longitude = -0.0015
        self._tiles = OrderedDict()
        self._size = _START_SIZE
        self._satellite = False

        # Desired viewing location and animation flags
        self._desired_zoom = self._zoom
        self._desired_latitude = self._latitude
        self._desired_longitude = self._longitude
        self._next_update = 100000

        # State for the background thread which reads in the tiles
        self._running = True
        self._updated = threading.Event()
        self._updated.set()
        self._oops = None
        self._thread = threading.Thread(target=self._get_tiles)
        self._thread.daemon = True
        self._thread.start()
        
        # a separate directory to store cached files.
        if not os.path.isdir('mapscache'):
            os.mkdir('mapscache')

    def _scale_coords(self, x, y, extent, xo, yo):
        """Convert from tile coordinates to "pixels" - i.e. text characters."""
        return xo + (x * self._size * 2 / extent), yo + ((extent - y) * self._size / extent)

    def _convert_longitude(self, longitude):
        """Convert from longitude to the x position in overall map."""
        return int((180 + longitude) * (2 ** self._zoom) * self._size / 360)

    def _convert_latitude(self, latitude):
        """Convert from latitude to the y position in overall map."""
        return int((180 - (180 / pi * log(tan(
            pi / 4 + latitude * pi / 360)))) * (2 ** self._zoom) * self._size / 360)

    def _inc_lat(self, latitude, delta):
        """Shift the latitude by the required number of pixels (i.e. text lines)."""
        y = self._convert_latitude(latitude)
        y += delta
        return 360 / pi * atan(
            exp((180 - y * 360 / (2 ** self._zoom) / self._size) * pi / 180)) - 90

    def _get_satellite_tile(self, x_tile, y_tile, z_tile):
        """Load up a single satellite image tile."""
        cache_file = "mapscache/{}.{}.{}.jpg".format(z_tile, x_tile, y_tile)
        if cache_file not in self._tiles:
            if not os.path.isfile(cache_file):
                url = _IMAGE_URL.format(z_tile, x_tile, y_tile, _KEY)
                data = requests.get(url).content
                with open(cache_file, 'wb') as f:
                    f.write(data)
            self._tiles[cache_file] = [
                x_tile, y_tile, z_tile,
                ColourImageFile(self._screen, cache_file, height=_START_SIZE, dither=True,
                                uni=self._screen.unicode_aware),
                True]
            if len(self._tiles) > _CACHE_SIZE:
                self._tiles.popitem(False)
            self._screen.force_update()

    def _get_vector_tile(self, x_tile, y_tile, z_tile):
        """Load up a single vector tile."""
        cache_file = "mapscache/{}.{}.{}.json".format(z_tile, x_tile, y_tile)
        if cache_file not in self._tiles:
            if os.path.isfile(cache_file):
                with open(cache_file, 'rb') as f:
                    tile = json.loads(f.read().decode('utf-8'))
            else:
                url = _VECTOR_URL.format(z_tile, x_tile, y_tile, _KEY)
                data = requests.get(url).content
                try:
                    tile = mapbox_vector_tile.decode(data)
                    with open(cache_file, mode='w') as f:
                        json.dump(literal_eval(repr(tile)), f)
                except DecodeError:
                    tile = None
            if tile:
                self._tiles[cache_file] = [x_tile, y_tile, z_tile, tile, False]
                if len(self._tiles) > _CACHE_SIZE:
                    self._tiles.popitem(False)
                self._screen.force_update()

    def _get_tiles(self):
        """Background thread to download map tiles as required."""
        while self._running:
            self._updated.wait()
            self._updated.clear()

            # Save off current view and find the nearest tile.
            satellite = self._satellite
            zoom = self._zoom
            size = self._size
            n = 2 ** zoom
            x_offset = self._convert_longitude(self._longitude)
            y_offset = self._convert_latitude(self._latitude)

            # Get the visible tiles around that location - getting most relevant first
            for x, y, z in [(0, 0, 0), (1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0),
                            (0, 0, -1), (0, 0, 1),
                            (1, 1, 0), (1, -1, 0), (-1, -1, 0), (-1, 1, 0)]:
                # Restart if we've already zoomed to another level
                if self._zoom != zoom:
                    break

                # Don't get tile if it falls off the grid
                x_tile = int(x_offset // size) + x
                y_tile = int(y_offset // size) + y
                z_tile = zoom + z
                if (x_tile < 0 or x_tile >= n or y_tile < 0 or y_tile >= n or
                        z_tile < 0 or z_tile > 20):
                    continue
                # noinspection PyBroadException
                try:

                    # Don't bother rendering if the tile is not visible
                    top = y_tile * size - y_offset + self._screen.height // 2
                    left = (x_tile * size - x_offset + self._screen.width // 4) * 2
                    if z == 0 and (left > self._screen.width or left + self._size * 2 < 0 or
                                   top > self._screen.height or top + self._size < 0):
                        continue

                    if satellite:
                        self._get_satellite_tile(x_tile, y_tile, z_tile)
                    else:
                        self._get_vector_tile(x_tile, y_tile, z_tile)
                # pylint: disable=broad-except
                except Exception:
                    self._oops = "{} - tile loc: {} {} {}".format(
                        traceback.format_exc(), x_tile, y_tile, z_tile)

                # Generally refresh screen after we've downloaded everything
                self._screen.force_update()

    def _get_features(self):
        """Decide which layers to render based on current zoom level and view type."""
        if self._satellite:
            return [("water", [], [])]
        elif self._zoom <= 2:
            return [
                ("water", [], []),
                ("marine_label", [], [1]),
            ]
        elif self._zoom <= 7:
            return [
                ("admin", [], []),
                ("water", [], []),
                ("road", ["motorway"], []),
                ("country_label", [], []),
                ("marine_label", [], [1]),
                ("state_label", [], []),
                ("place_label", [], ["city", "town"]),
            ]
        elif self._zoom <= 10:
            return [
                ("admin", [], []),
                ("water", [], []),
                ("road", ["motorway", "motorway_link", "trunk"], []),
                ("country_label", [], []),
                ("marine_label", [], [1]),
                ("state_label", [], []),
                ("place_label", [], ["city", "town"]),
            ]
        else:
            return [
                ("landuse", ["agriculture", "grass", "park"], []),
                ("water", [], []),
                ("waterway", ["river", "canal"], []),
                ("building", [], []),
                ("road",
                 ["motorway", "motorway_link", "trunk", "primary", "secondary"]
                 if self._zoom <= 14 else
                 ["motorway", "motorway_link", "trunk", "primary", "secondary", "tertiary",
                  "link", "street", "tunnel"],
                 []),
                ("poi_label", [], []),
            ]

    def _draw_lines_internal(self, coords, colour, bg):
        """Helper to draw lines connecting a set of nodes that are scaled for the Screen."""
        for i, (x, y) in enumerate(coords):
            if i == 0:
                self._screen.move(x, y)
            else:
                self._screen.draw(x, y, colour=colour, bg=bg, thin=True)

    def _draw_polygons(self, feature, bg, colour, extent, polygons, xo, yo):
        """Draw a set of polygons from a vector tile."""
        coords = []
        for polygon in polygons:
            coords.append([self._scale_coords(x, y, extent, xo, yo) for x, y in polygon])
        # Polygons are expensive to draw and the buildings layer is huge - so we convert to
        # lines in order to process updates fast enough to animate.
        if "type" in feature["properties"] and "building" in feature["properties"]["type"]:
            for line in coords:
                self._draw_lines_internal(line, colour, bg)
        else:
            self._screen.fill_polygon(coords, colour=colour, bg=bg)

    def _draw_lines(self, bg, colour, extent, line, xo, yo):
        """Draw a set of lines from a vector tile."""
        coords = [self._scale_coords(x, y, extent, xo, yo) for x, y in line]
        self._draw_lines_internal(coords, colour, bg)

    def _draw_feature(self, feature, extent, colour, bg, xo, yo):
        """Draw a single feature from a layer in a vector tile."""
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            self._draw_polygons(feature, bg, colour, extent, geometry["coordinates"], xo, yo)
        elif feature["geometry"]["type"] == "MultiPolygon":
            for multi_polygon in geometry["coordinates"]:
                self._draw_polygons(feature, bg, colour, extent, multi_polygon, xo, yo)
        elif feature["geometry"]["type"] == "LineString":
            self._draw_lines(bg, colour, extent, geometry["coordinates"], xo, yo)
        elif feature["geometry"]["type"] == "MultiLineString":
            for line in geometry["coordinates"]:
                self._draw_lines(bg, colour, extent, line, xo, yo)
        elif feature["geometry"]["type"] == "Point":
            x, y = self._scale_coords(
                geometry["coordinates"][0], geometry["coordinates"][1], extent, xo, yo)
            text = u" {} ".format(feature["properties"]["name_en"])
            self._screen.print_at(text, int(x - len(text) / 2), int(y), colour=colour, bg=bg)

    def _draw_tile_layer(self, tile, layer_name, c_filters, colour, t_filters, x, y, bg):
        """Draw the visible geometry in the specified map tile."""
        # Don't bother rendering if the tile is not visible
        left = (x + self._screen.width // 4) * 2
        top = y + self._screen.height // 2
        if (left > self._screen.width or left + self._size * 2 < 0 or
                top > self._screen.height or top + self._size < 0):
            return 0

        # Not all layers are available in every tile.
        try:
            _layer = tile[layer_name]
            _extent = float(_layer["extent"])
        except KeyError:
            return 0

        for _feature in _layer["features"]:
            try:
                if c_filters and _feature["properties"]["class"] not in c_filters:
                    continue
                if (t_filters and _feature["type"] not in t_filters and
                        _feature["properties"]["type"] not in t_filters):
                    continue
                self._draw_feature(
                    _feature, _extent, colour, bg,
                    (x + self._screen.width // 4) * 2, y + self._screen.height // 2)
            except KeyError:
                pass
        return 1

    def _draw_satellite_tile(self, tile, x, y):
        """Draw a satellite image tile to screen."""
        image, colours = tile.rendered_text
        for (i, line) in enumerate(image):
            self._screen.paint(line, x, y + i, colour_map=colours[i])
        return 1

    def _draw_tiles(self, x_offset, y_offset, bg):
        """Render all visible tiles a layer at a time."""
        count = 0
        for layer_name, c_filters, t_filters in self._get_features():
            colour = (self._256_PALETTE[layer_name]
                      if self._screen.colours >= 256 else self._16_PALETTE[layer_name])
            for x, y, z, tile, satellite in sorted(self._tiles.values(), key=lambda k: k[0]):
                # Don't draw the wrong type or zoom of tile.
                if satellite != self._satellite or z != self._zoom:
                    continue

                # Convert tile location into pixels and draw the tile.
                x *= self._size
                y *= self._size
                if satellite:
                    count += self._draw_satellite_tile(
                        tile,
                        int((x-x_offset + self._screen.width // 4) * 2),
                        int(y-y_offset + self._screen.height // 2))
                else:
                    count += self._draw_tile_layer(tile, layer_name, c_filters, colour, t_filters,
                                                   x - x_offset, y - y_offset, bg)
        return count

    def _zoom_map(self, zoom_out=True):
        """Animate the zoom in/out as appropriate for the displayed map tile."""
        size_step = 1 / _ZOOM_STEP if zoom_out else _ZOOM_STEP
        self._next_update = 1
        if self._satellite:
            size_step **= _ZOOM_ANIMATION_STEPS
        self._size *= size_step
        if self._size <= _ZOOM_OUT_SIZE:
            if self._zoom > 0:
                self._zoom -= 1
                self._size = _START_SIZE
            else:
                self._size = _ZOOM_OUT_SIZE
        elif self._size >= _ZOOM_IN_SIZE:
            if self._zoom < 20:
                self._zoom += 1
                self._size = _START_SIZE
            else:
                self._size = _ZOOM_IN_SIZE

    def _move_to_desired_location(self):
        """Animate movement to desired location on map."""
        self._next_update = 100000
        x_start = self._convert_longitude(self._longitude)
        y_start = self._convert_latitude(self._latitude)
        x_end = self._convert_longitude(self._desired_longitude)
        y_end = self._convert_latitude(self._desired_latitude)
        if sqrt((x_end - x_start) ** 2 + (y_end - y_start) ** 2) > _START_SIZE // 4:
            self._zoom_map(True)
        elif self._zoom != self._desired_zoom:
            self._zoom_map(self._desired_zoom < self._zoom)
        if self._longitude != self._desired_longitude:
            self._next_update = 1
            if self._desired_longitude < self._longitude:
                self._longitude = max(self._longitude - 360 / 2 ** self._zoom / self._size * 2,
                                      self._desired_longitude)
            else:
                self._longitude = min(self._longitude + 360 / 2 ** self._zoom / self._size * 2,
                                      self._desired_longitude)
        if self._latitude != self._desired_latitude:
            self._next_update = 1
            if self._desired_latitude < self._latitude:
                self._latitude = max(self._inc_lat(self._latitude, 2), self._desired_latitude)
            else:
                self._latitude = min(self._inc_lat(self._latitude, -2), self._desired_latitude)
        if self._next_update == 1:
            self._updated.set()

    def _update(self, frame_no):
        """Draw the latest set of tiles to the Screen."""
        # Check for any fatal errors from the background thread and quit if we hit anything.
        if self._oops:
            raise RuntimeError(self._oops)

        # Calculate new positions for animated movement.
        self._move_to_desired_location()

        # Re-draw the tiles - if we have any suitable ones downloaded.
        count = 0
        x_offset = self._convert_longitude(self._longitude)
        y_offset = self._convert_latitude(self._latitude)
        if self._tiles:
            # Clear the area first.
            bg = 253 if self._screen.unicode_aware and self._screen.colours >= 256 else 0
            for y in range(self._screen.height):
                self._screen.print_at("." * self._screen.width, 0, y, colour=bg, bg=bg)

            # Now draw all the available tiles.
            count = self._draw_tiles(x_offset, y_offset, bg)

        # Just a few pointers on what the user should do...
        if count == 0:
            self._screen.centre(" Loading - please wait... ", self._screen.height // 2, 1)

        self._screen.centre("Press '?' for help.", 0, 1)
        if _KEY == "":
            footer = "Using local cached data - go to https://www.mapbox.com/ and get a free key."
        else:
            footer = u"Zoom: {} Location: {:.6}, {:.6} Maps: © Mapbox, © OpenStreetMap".format(
                self._zoom, self._longitude, self._latitude)
        self._screen.centre(footer, self._screen.height - 1, 1)

        return count

    def process_event(self, event):
        """User input for the main map view."""
        if isinstance(event, KeyboardEvent):
            if event.key_code in [Screen.ctrl("m"), Screen.ctrl("j")]:
                self._scene.add_effect(
                    EnterLocation(
                        self._screen, self._longitude, self._latitude, self._on_new_location))
            elif event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord('t'), ord('T')]:
                self._satellite = not self._satellite
                if self._satellite:
                    self._size = _START_SIZE
            elif event.key_code == ord("?"):
                self._scene.add_effect(PopUpDialog(self._screen, _HELP, ["OK"]))
            elif event.key_code == ord("+") and self._zoom <= 20:
                if self._desired_zoom < 20:
                    self._desired_zoom += 1
            elif event.key_code == ord("-") and self._zoom >= 0:
                if self._desired_zoom > 0:
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

    def _on_new_location(self, form):
        """Set a new desired location entered in the pop-up form."""
        self._desired_longitude = float(form.data["long"])
        self._desired_latitude = float(form.data["lat"])
        self._desired_zoom = 13
        self._screen.force_update()

    # noinspection PyUnusedLocal
    # pylint: disable=unused-argument
    def clone(self, new_screen, new_scene):
        # On resize, there will be a new Map - kill the thread in this one.
        self._running = False
        self._updated.set()

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


def demo(screen, scene):
    screen.play([Scene([Map(screen)], -1)], stop_on_resize=True, start_scene=scene)


if __name__ == "__main__":
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
