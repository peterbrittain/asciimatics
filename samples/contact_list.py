from asciimatics.widgets import Frame, ListBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys
import sqlite3


class ContactModel(object):
    def __init__(self):
        # Create a database in RAM
        self._db = sqlite3.connect(':memory:')

        # Create the basic contact table.
        self._db.cursor().execute('''
            CREATE TABLE contacts(
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                address TEXT,
                email TEXT unique,
                notes TEXT)
        ''')
        self._db.commit()

        # Add a dummy user
        self.add({
            "name": "Peter",
            "phone": "5055555555",
            "address": "Somewhere",
            "email": "a@b.com",
            "notes": "Some stuff"
        })

    def add(self, contact):
        self._db.cursor().execute('''
            INSERT INTO contacts(name, phone, address, email, notes)
                VALUES(:name, :phone, :address, :email, :notes)''',
                  contact)
        self._db.commit()

    def get_summary(self):
        contacts = self._db.cursor().execute("SELECT name from contacts").fetchall()
        return {"contacts": [x[0] for x in contacts]}


class ListView(Frame):
    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       model,
                                       screen.height,
                                       screen.width)
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Label("Contact list:"))
        layout.add_widget(Divider())
        layout.add_widget(ListBox(10, name="contacts"))
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add"), 1)
        layout2.add_widget(Button("Edit"), 2)
        layout2.add_widget(Button("Delete"), 3)
        self.fix()


def demo(screen):
    contacts = ContactModel()

    scenes = [
        Scene([ListView(screen, contacts.get_summary())], -1),
        # Scene([ContactView(screen)], -1)
    ]

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
