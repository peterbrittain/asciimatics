from builtins import dict
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
        self._db.row_factory = sqlite3.Row

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

        # Current contact when editing.
        self.current_id = None

        # Add a dummy user
        self.add({
            "name": "Peter",
            "phone": "5055555555",
            "address": "Somewhere",
            "email": "a@b.com",
            "notes": ["Some stuff"]
        })
        self.add({
            "name": "Paul",
            "phone": "5055555555",
            "address": "Somewhere",
            "email": "a@c.com",
            "notes": ["Some stuff"]
        })

    @staticmethod
    def _fix_fields(contact):
        for key, value in contact.items():
            if key == "notes":
                contact[key] = "\n".join(value)

    def add(self, contact):
        # Flatten lists for sqlite
        self._fix_fields(contact)

        # Now write to the DB
        self._db.cursor().execute('''
            INSERT INTO contacts(name, phone, address, email, notes)
            VALUES(:name, :phone, :address, :email, :notes)''',
                                  contact)
        self._db.commit()

    def get_summary(self):
        return self._db.cursor().execute(
            "SELECT name, id from contacts").fetchall()

    def get_contact(self, contact_id):
        return self._db.cursor().execute(
            "SELECT * from contacts where id=?", str(contact_id)).fetchone()

    def get_current_contact(self):
        if self.current_id is None:
            return {}
        else:
            # Convert DB Row to genuine dict with list objects for multi-line
            # entries
            result = dict()
            contact = self.get_contact(self.current_id)
            for key in contact.keys():
                if key == "notes":
                    result[key] = contact[key].split("\n")
                else:
                    result[key] = contact[key]
            return result

    def update_current_contact(self, details):
        if self.current_id is None:
            self.add(details)
        else:
            # Flatten lists for sqlite
            self._fix_fields(details)

            self._db.cursor().execute('''
                UPDATE contacts SET name=:name, phone=:phone, address=:address,
                email=:email, notes=:notes WHERE id=:id''',
                                      details)
            self._db.commit()


class ListView(Frame):

    #: Data cache for the list of contacts
    _CACHE = {}

    def __init__(self, screen, model):
        super(ListView, self).__init__(screen,
                                       self._CACHE,
                                       screen.height,
                                       screen.width)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(Label("Contact list:"))
        layout.add_widget(Divider())
        layout.add_widget(ListBox(10, model.get_summary(), name="contacts"))
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 1)
        layout2.add_widget(Button("Edit", self._edit), 2)
        layout2.add_widget(Button("Delete", self._delete), 3)
        self.fix()

    def reset(self):
        # TODO: Fix this hack.
        self._CACHE["contacts"] = self._model.get_summary()
        self._data = self._CACHE
        # TODO: Need to fix up the way ListBox options get reset.
        super(ListView, self).reset()

    def _add(self):
        self._model.current_id = None
        raise NextScene()

    def _edit(self):
        self.save()
        self._model.current_id = self._CACHE["contacts"]
        raise NextScene()

    def _delete(self):
        # TODO: Remove the entry from the model.
        raise RuntimeError("Not implemented yet!")


class ContactView(Frame):

    #: Data cache for the list of contacts
    _CACHE = {}

    def __init__(self, screen, model):
        super(ContactView, self).__init__(screen,
                                          self._CACHE,
                                          screen.height,
                                          screen.width)
        # Save off the model that accesses the contacts database.
        self._model = model

        # Create the form for displaying the list of contacts.
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
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def reset(self):
        # TODO: Fix this hack.
        self._CACHE = self._model.get_current_contact()
        self._data = self._CACHE
        super(ContactView, self).reset()

    def _ok(self):
        self.save()
        self._model.update_current_contact(self._CACHE)
        raise NextScene()

    def _cancel(self):
        raise NextScene()


def demo(screen):
    contacts = ContactModel()

    scenes = [
        Scene([ListView(screen, contacts)], -1),
        Scene([ContactView(screen, contacts)], -1)
    ]

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
