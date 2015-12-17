from asciimatics.widgets import Frame, ListBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button, TextBox
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene
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

    def get_contact(self):
        # TODO: Fix up model for reading one contact
        return {}


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
        layout2.add_widget(Button("Add", self._add), 1)
        layout2.add_widget(Button("Edit", self._edit), 2)
        layout2.add_widget(Button("Delete", self._delete), 3)
        self.fix()

    def _add(self):
        # TODO: Clear out contact view
        raise NextScene()

    def _edit(self):
        # TODO: Populate contact view
        raise NextScene()

    def _delete(self):
        # TODO: Remove the entry from the model.
        raise RuntimeError("Not implemented yet!")


class ContactView(Frame):
    def __init__(self, screen, model):
        super(ContactView, self).__init__(screen,
                                          model,
                                          screen.height,
                                          screen.width)
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Text("Name:", "name"))
        layout.add_widget(Text("Address:", "address"))
        layout.add_widget(Text("Phone number:", "phone"))
        layout.add_widget(Text("Email address:", "email"))
        layout.add_widget(TextBox(5, "Notes:", "notes"))
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._save), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def _save(self):
        # TODO: Save back to the model.
        raise NextScene()

    def _cancel(self):
        raise NextScene()


def demo(screen):
    contacts = ContactModel()

    scenes = [
        Scene([ListView(screen, contacts.get_summary())], -1),
        Scene([ContactView(screen, contacts.get_contact())], -1)
    ]

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
