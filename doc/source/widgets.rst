User Interfaces
===============

Introduction
------------
The asciimatics package provides a `widgets` sub-package that allows you to
create interactive text user interfaces.  At its heart, the logic is quite
simple, reusing concepts from standard web and desktop GUI frameworks.

1. The basic building block for your text UI is a `Widget`.  There is a set
   of standard ones provided by asciimatics, but you can create a custom set if
   needed.  The basic set has strong parallels with simple web input forms -
   e.g. buttons, check boxes, etc.
2. The `Widgets` need to be arranged on the `Screen` and rearranged whenever it
   is resized.  The `Layout` class handles this for you.  You just need to add
   your `Widgets` to one.
3. You then need to display the `Layouts`.  To do this, you must add them to a
   `Frame`.  This class is an `Effect` and so can be used in any `Scene`
   alongside any other `Effect`. The `Frame` will draw any parts of the
   `Layouts` it contains that are visible within its boundaries.  The net result
   is that it begins to look a bit like a window in GUI frameworks.

And that's it!  You can set various callbacks to get triggered when key events
occur - e.g. changes to values, buttons get clicked, etc. - and use these to
trigger your application processing.  For an example, see the contact_list.py
sample provided.

Model/View Design
-----------------
Before we jump into exactly what all the objects are and what they do for you,
it is important to understand how you must put them together to make the best
use of them.

The underlying Screen/Scene/Effect design of asciimatics means that objects
regularly get thrown away and recreated - especially when the Screen is
resized.  It is therefore vital to separate your data model from your code to
display it on the screen.

This split is often (wrongly) termed the `MVC
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`__ model,
but a more accurate description is `Separated Presentation
<http://martinfowler.com/eaaDev/SeparatedPresentation.html>`__.  No matter what
term you use, the concept is easy: use a separate class to handle your
persistent data storage.

In more concrete terms, let's have a closer look at the contact_list sample.
This consists of 3 basic classes:

1. `ContactModel`: This is the model.  It stores simple contact details in a
   sqlite in-memory database and provides a simple create/read/update/delete
   interface to manipulate any contact.  Note that you don't have to be this
   heavy-weight with the data storage; a simple class to wrap a list of
   dictionaries would also suffice - but doesn't look as professional for a
   demo!

.. code-block:: python

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
                    email TEXT,
                    notes TEXT)
            ''')
            self._db.commit()

            # Current contact when editing.
            self.current_id = None

        def add(self, contact):
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
                return self.get_contact(self.current_id)

        def update_current_contact(self, details):
            if self.current_id is None:
                self.add(details)
            else:
                self._db.cursor().execute('''
                    UPDATE contacts SET name=:name, phone=:phone, address=:address,
                    email=:email, notes=:notes WHERE id=:id''',
                                          details)
                self._db.commit()

        def delete_contact(self, contact_id):
            self._db.cursor().execute('''
                DELETE FROM contacts WHERE id=:id''', {"id": contact_id})
            self._db.commit()

2. `ListView`: This is the main view.  It queries the `ContactModel` for the
   list of known contacts and displays them in a list, complete with some extra
   buttons to add/edit/delete contacts.

..  code-block:: python

    class ListView(Frame):
        def __init__(self, screen, model):
            super(ListView, self).__init__(screen,
                                           screen.height * 2 // 3,
                                           screen.width * 2 // 3,
                                           on_load=self._reload_list,
                                           hover_focus=True,
                                           title="Contact List")
            # Save off the model that accesses the contacts database.
            self._model = model

            # Create the form for displaying the list of contacts.
            self._list_view = ListBox(
                -3, model.get_summary(), name="contacts", on_select=self._on_pick)
            self._edit_button = Button("Edit", self._edit)
            self._delete_button = Button("Delete", self._delete)
            layout = Layout([100], fill_frame=True)
            self.add_layout(layout)
            layout.add_widget(self._list_view)
            layout.add_widget(Divider())
            layout2 = Layout([1, 1, 1, 1])
            self.add_layout(layout2)
            layout2.add_widget(Button("Add", self._add), 0)
            layout2.add_widget(self._edit_button, 1)
            layout2.add_widget(self._delete_button, 2)
            layout2.add_widget(Button("Quit", self._quit), 3)
            self.fix()

        def _on_pick(self):
            self._edit_button.disabled = self._list_view.value is None
            self._delete_button.disabled = self._list_view.value is None

        def _reload_list(self):
            self._list_view.options = self._model.get_summary()
            self._model.current_id = None

        def _add(self):
            self._model.current_id = None
            raise NextScene("Edit Contact")

        def _edit(self):
            self.save()
            self._model.current_id = self.data["contacts"]
            raise NextScene("Edit Contact")

        def _delete(self):
            self.save()
            self._model.delete_contact(self.data["contacts"])
            self._reload_list()

        @staticmethod
        def _quit():
            raise StopApplication("User pressed quit")

3. `ContactView`: This is the detailed view.  It queries the `ContactModel` for
   the current contact to be displayed at the start (which may be none if the
   user is adding a contact) and writes any changes back to the model when the
   user clicks OK.

.. code-block:: python

    class ContactView(Frame):
        def __init__(self, screen, model):
            super(ContactView, self).__init__(screen,
                                              screen.height * 2 // 3,
                                              screen.width * 2 // 3,
                                              hover_focus=True,
                                              title="Contact Details")
            # Save off the model that accesses the contacts database.
            self._model = model

            # Create the form for displaying the list of contacts.
            layout = Layout([100], fill_frame=True)
            self.add_layout(layout)
            layout.add_widget(Text("Name:", "name"))
            layout.add_widget(Text("Address:", "address"))
            layout.add_widget(Text("Phone number:", "phone"))
            layout.add_widget(Text("Email address:", "email"))
            layout.add_widget(TextBox(5, "Notes:", "notes", as_string=True))
            layout2 = Layout([1, 1, 1, 1])
            self.add_layout(layout2)
            layout2.add_widget(Button("OK", self._ok), 0)
            layout2.add_widget(Button("Cancel", self._cancel), 3)
            self.fix()

        def reset(self):
            # Do standard reset to clear out form, then populate with new data.
            super(ContactView, self).reset()
            self.data = self._model.get_current_contact()

        def _ok(self):
            self.save()
            self._model.update_current_contact(self.data)
            raise NextScene("Main")

        @staticmethod
        def _cancel():
            raise NextScene("Main")

Displaying your UI
------------------
OK, so you want to do something a little more interactive with your user.  The
first thing you have to decide is what information you want to get from them
and how you're going to achieve that.  In short, you need to decide:

1. What data you want them to be able to enter - e.g. their name.
2. How you want to break that down into fields - e.g. first name, last name.
3. What the natural representation of those fields would be - e.g. text strings.

At this point, you can now decide which Widgets you want to use.  The standard
selection is as follows.

========================    ====================================================
Widget type                 Description
========================    ====================================================
:py:obj:`.Button`           Action buttons - e.g. ok/cancel/etc.
:py:obj:`.CheckBox`         Simple yes/no tick boxes.
:py:obj:`.Divider`          A spacer between widgets (for aesthetics).
:py:obj:`.Label`            A label for a group of related widgets.
:py:obj:`.ListBox`          A list of possible options from which the user can
                            select one value.
:py:obj:`.RadioButtons`     A list of radio buttons.  These allow the user to
                            select one value from a list of options.
:py:obj:`.Text`             A single line of editable text.
:py:obj:`.TextBox`          A multi-line box of editable text.
========================    ====================================================

Asciimatics will automatically arrange these for you with just a little extra
help.  All you need to do is decide how many columns you want for your fields
and which fields should be in which columns.  To tell asciimatics what to do
you create a `Layout` (or more than one if you want a more complex
structure where different parts of the screen need differing column counts) and
associate it with the `Frame` where you plan to display it.

For example, this will create a Frame that is 80x20 characters and define 4
columns that are each 20 columns wide.

.. code-block:: python

    frame = Frame(screen, 80, 20, has_border=False)
    layout = Layout([1, 1, 1, 1])
    frame.add_layout(layout)

Once you have a Layout, you can add Widgets to the relevant column.  For
example, this will add a button to the middle first and last columns.

.. code-block:: python

    layout2.add_widget(Button("OK", self._ok), 0)
    layout2.add_widget(Button("Cancel", self._cancel), 3)

If you ant to put a standard label on all your input fields, that's fine too;
asciimatics will decide how big your label needs to be across all fields in the
same column and then indent them all to create a more aesthetically pleasing
layout.  For example, this will provide a single column with labels for each
fields, indenting all the fields to the same depth.

.. code-block:: python

    layout = Layout([100])
    self.add_layout(layout)
    layout.add_widget(Text("Name:", "name"))
    layout.add_widget(Text("Address:", "address"))
    layout.add_widget(Text("Phone number:", "phone"))
    layout.add_widget(Text("Email address:", "email"))
    layout.add_widget(TextBox(5, "Notes:", "notes", as_string=True))

Layouts in more detail
~~~~~~~~~~~~~~~~~~~~~~
If you need to do something more complex, you can use multiple Layouts.
Asciimatics uses the following logic to determine the location of Widgets.

1.  The `Frame` owns one or more `Layouts`.  The `Layouts` stack one above each
    other when displayed - i.e. the first `Layout` in the `Frame` is above the
    second, etc.
2.  Each `Layout` defines smoe horizontal constraints by defining columns as a
    proportion of the full `Frame` width.
3.  The `Widgets` are assigned a column within the `Layout` that owns them.
4.  The `Layout` then decides the exact size and location to make each
    `Widget` best fit the visible space as constrained by the above.

For example::

    +------------------------------------------------------------------------+
    |Screen..................................................................|
    |........................................................................|
    |...+----------------------------------------------------------------+...|
    |...|Frame                                                           |...|
    |...|+--------------------------------------------------------------+|...|
    |...||Layout 1                                                      ||...|
    |...|+--------------------------------------------------------------+|...|
    |...|+------------------------------+-------------------------------+|...|
    |...||Layout 2                      |                               ||...|
    |...|| - Column 1                   | - Column 2                    ||...|
    |...|+------------------------------+-------------------------------+|...|
    |...|+-------------+---------------------------------+--------------+|...|
    |...||Layout 3     | < Widget 1 >                    |              ||...|
    |...||             | ...                             |              ||...|
    |...||             | < Widget N >                    |              ||...|
    |...|+-------------+---------------------------------+--------------+|...|
    |...+----------------------------------------------------------------+...|
    |........................................................................|
    +------------------------------------------------------------------------+

This consists of a single `Frame` with 3 `Layouts`.  The first is a single,
full-width column, the second has two 50% width columns and the third consists
of 3 columns of relative size 25:50:25.  The last actually contains some Widgets
in the second column (though this is just for illustration purposes as we'd
expect most Layouts to have some Widgets in them).

Getting values
--------------
Now that you have a `Frame` with some `Widgets` in it and the user is filling
them in, how do you find out what they entered?  There are 2 basic ways to do
this:

1. You can query each Widget directly, using the `value` property.  This returns
   the current value the user has entered at any time (even when the Frame is
   not active).  Note that it may be `None` for those `Widgets` where there is
   no value - e.g. buttons.
2. You can query the `Frame`.   @@@ Add details

@@@TODO: Fix up the rest of this file to follow more task oriented structure.

Frames
------
As already noted at the start, the fundamental class you need to create your UI
is a :py:obj:`.Frame`.  This is the :py:obj:`.Effect` that will draw all the
visible widgets (using the Layouts that contain them) and routes any user
input to the correct `Widget`.

The `Frame` provides most of the generic configuration options for your text UI.
In particular, it determines:

1. Your colour scheme - which is defined by the `palette` property.
2. The dimensions of the window in which to display your UI.
3. Whether the mouse will move focus by simply hovering over a `Widget` or by
   clicking on it.
4. What (if anything) to do when the Frame is loaded/reloaded, through the
   `on_load` parameter.

These options (and a few more that typically determine how the Frame itself is
drawn) are all documented in the :py:obj:`.Frame` API reference.

In addition, it also provides the `save()` method and `data` property.  These
allow the Frame to save off all the data that the user has entered into the
widgets inside this Frame and return them as a Python dictionary.


Colour schemes
--------------
@@@ TODO


Common keys
-----------
@@@ TODO


Flow control
------------
@@@ TODO - scene navigation, use of callbacks and pup-up dialogs.


Screen resizing
---------------
@@@ TODO


Custom widgets
--------------
@@@ TODO