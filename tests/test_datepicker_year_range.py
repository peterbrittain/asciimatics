from datetime import date
from unittest.mock import MagicMock

import pytest

from asciimatics.event import KeyboardEvent
from asciimatics.scene import Scene
from asciimatics.screen import Canvas, Screen
from asciimatics.widgets import DatePicker, Frame, Layout


@pytest.mark.parametrize(
    "years",
    [
        range(2016, 2019),
        range(2017, 2018),
        range(2013, 2022, 2),
        range(2000, 2002),
        range(2030, 2020, -1),
        None,
    ],
)
def test_datepicker_uses_configured_year_range(years):
    screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
    canvas = Canvas(screen, 10, 40, 0, 0)
    frame = Frame(canvas, 10, 40)
    layout = Layout([1])
    frame.add_layout(layout)
    picker = layout.add_widget(DatePicker(name="date", year_range=years))
    frame.fix()
    scene = Scene([frame], duration=-1)
    scene.reset()
    picker.value = date(2017, 6, 15)
    picker.process_event(KeyboardEvent(Screen.ctrl("m")))
    popup = scene.effects[-1]
    expected = years if years is not None else range(1967, 2067)
    assert [value for _, value in popup._years.options] == list(expected)
    assert popup._years.value == min(expected, key=lambda year: abs(year - 2017))
    popup._years.value = list(expected)[-1]
    popup._on_close(cancelled=False)
    assert picker.value == date(list(expected)[-1], 6, 15)


def test_datepicker_rejects_an_empty_year_range():
    screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
    frame = Frame(Canvas(screen, 10, 40, 0, 0), 10, 40)
    layout = Layout([1])
    frame.add_layout(layout)
    picker = layout.add_widget(DatePicker(name="date", year_range=range(0)))
    frame.fix()
    scene = Scene([frame], duration=-1)
    scene.reset()
    with pytest.raises(ValueError, match="year_range must contain at least one year"):
        picker.process_event(KeyboardEvent(Screen.ctrl("m")))
