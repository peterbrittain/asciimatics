User Interfaces
===============

Introduction
------------

Asciimatics provides a `widgets` sub-package that allows you to create interactive text user
interfaces.  At its heart, the logic is quite simple, reusing concepts from standard web and
desktop GUI frameworks.

1. The basic building block for your text UI is a `Widget`.  There is a set of standard ones
   provided by asciimatics, but you can create a custom set if needed.  The basic set has strong
   parallels with simple web input forms - e.g. buttons, check boxes, etc.
2. The `Widgets` need to be arranged on the `Screen` and rearranged whenever it is resized.  The
   `Layout` class handles this for you.  You just need to add your `Widgets` to one.
3. You then need to display the `Layouts`.  To do this, you must add them to a `Frame`.  This class
   is an `Effect` and so can be used in any `Scene` alongside any other `Effect`. The `Frame` will
   draw any parts of the `Layouts` it contains that are visible within its boundaries.  The net
   result is that it begins to look a bit like a window in GUI frameworks.

And that's it!  You can set various callbacks to get triggered when key events occur - e.g. changes
to values, buttons get clicked, etc. - and use these to trigger your application processing.  For
an example, see the contact_list.py sample provided - which will look a bit like this:

.. image:: contacts.png
    :alt: Screen shot of the contacts list sample

Common keys
~~~~~~~~~~~
When navigating around a Frame, you can normally use the following keys.

===================  ==============================================================================
Key                  Action
===================  ==============================================================================
Tab                  Move to the next Widget in the Frame
Backtab (shift+tab)  Move to the previous Widget in the Frame
Up arrow             Move to the nearest Widget above the current focus.
Down arrow           Move to the nearest Widget below the current focus.
Left arrow           Move to the nearest Widget to the left of the current focus.
Right arrow          Move to the nearest Widget to the right of the current focus.
Space or Return      Select the current Widget - e.g. click a Button, or pop-up a list of options.
===================  ==============================================================================

.. warning::

    Please note that asciimatics will not allow you to navigate to a disabled widget.  Instead
    it will select the next enabled widget when traversing the Frame.

However, some widgets (e.g. text editing widgets) have their own logic for handling the cursor
key actions, which override the common navigation.  In such cases, tab/backtab will still navigate
out of the Widgets.

In addition you can also use the following extra keys inside text editing widgets.

===================  ==========================================================
Key                  Action
===================  ==========================================================
Home/End             Move to the start/end of the current line.
Delete               Delete the character under the cursor.
Backspace            Delete the character before the cursor.
===================  ==========================================================

Model/View Design
-----------------
Before we jump into exactly what all the objects are and what they do for you, it is important to
understand how you must put them together to make the best use of them.

The underlying Screen/Scene/Effect design of asciimatics means that objects regularly get thrown
away and recreated - especially when the Screen is resized.  It is therefore vital to separate your
data model from your code to display it on the screen.

This split is often (wrongly) termed the `MVC
<https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller>`__ model, but a more accurate
description is `Separated Presentation
<http://martinfowler.com/eaaDev/SeparatedPresentation.html>`__.  No matter what term you use, the
concept is easy: use a separate class to handle your persistent data storage.

In more concrete terms, let's have a closer look at the contact_list sample.  This consists of 3
basic classes:

1. `ContactModel`: This is the model.  It stores simple contact details in a sqlite in-memory
   database and provides a simple create/read/update/delete interface to manipulate any contact.
   Note that you don't have to be this heavy-weight with the data storage; a simple class to wrap a
   list of dictionaries would also suffice - but doesn't look as professional for a demo!

.. container:: toggle

    .. container:: header

        **Show/hide code**

    .. code-block:: python

        class ContactModel():
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
                    return {"name": "", "address": "", "phone": "", "email": "", "notes": ""}
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

2. `ListView`: This is the main view.  It queries the `ContactModel` for the list of known contacts
   and displays them in a list, complete with some extra buttons to add/edit/delete contacts.

.. container:: toggle

    .. container:: header

        **Show/hide code**

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
                    Widget.FILL_FRAME,
                    model.get_summary(), name="contacts", on_select=self._on_pick)
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

3. `ContactView`: This is the detailed view.  It queries the `ContactModel` for the current contact
   to be displayed when it is reset (note: there may be no contact if the user is adding a contact) and writes
   any changes back to the model when the user clicks OK.

.. container:: toggle

    .. container:: header

        **Show/hide code**

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
OK, so you want to do something a little more interactive with your user.  The first thing you need
to decide is what information you want to get from them and how you're going to achieve that.  In
short:

1. What data you want them to be able to enter - e.g. their name.
2. How you want to break that down into fields - e.g. first name, last name.
3. What the natural representation of those fields would be - e.g. text strings.

At this point, you can now decide which Widgets you want to use.  The standard selection is as
follows.

============================= =====================================================================
Widget type                   Description
============================= =====================================================================
:py:obj:`.Button`             Action buttons - e.g. ok/cancel/etc.
:py:obj:`.CheckBox`           Simple yes/no tick boxes.
:py:obj:`.DatePicker`         A single-line widget for selecting a date (using a pop-up list).
:py:obj:`.Divider`            A spacer between widgets (for aesthetics).
:py:obj:`.DropdownList`       A single-line widget that pops up a list from which the user can
                              select a single value.
:py:obj:`.FileBrowser`        A multi-line widget for listing the local file system.
:py:obj:`.Label`              A label for a group of related widgets.
:py:obj:`.ListBox`            A list of possible options from which users can select one value.
:py:obj:`.MultiColumnListBox` Like a ListBox, but for displaying tabular data.
:py:obj:`.RadioButtons`       A list of radio buttons.  These allow users to select one value from
                              a list of options.
:py:obj:`.Text`               A single line of editable text.
:py:obj:`.TextBox`            A multi-line box of editable text.
:py:obj:`.TimePicker`         A single-line widget for selecting a time (using a pop-up list).
:py:obj:`.VerticalDivider`    A vertical line divider - useful for providing a visual marker
                              between columns in a Layout.
============================= =====================================================================

.. note:: You can use the `hide_char` option on Text widgets to hide sensitive data - e.g. for
          passwords.

Asciimatics will automatically arrange these for you with just a little extra help.  All you need
to do is decide how many columns you want for your fields and which fields should be in which
columns.  To tell asciimatics what to do you create a `Layout` (or more than one if you want a more
complex structure where different parts of the screen need differing column counts) and associate
it with the `Frame` where you will display it.

For example, this will create a Frame that is 80x20 characters and define 4 columns that are each
20 columns wide:

.. code-block:: python

    frame = Frame(screen, 80, 20, has_border=False)
    layout = Layout([1, 1, 1, 1])
    frame.add_layout(layout)

Once you have a Layout, you can add Widgets to the relevant column.  For example, this will add a
button to the first and last columns:

.. code-block:: python

    layout.add_widget(Button("OK", self._ok), 0)
    layout.add_widget(Button("Cancel", self._cancel), 3)

If you want to put a standard label on all your input fields, that's fine too; asciimatics will
decide how big your label needs to be across all fields in the same column and then indent them all
to create a more aesthetically pleasing layout.  For example, this will provide a single column
with labels for each field, indenting all of the fields to the same depth:

.. code-block:: python

    layout = Layout([100])
    frame.add_layout(layout)
    layout.add_widget(Text("Name:", "name"))
    layout.add_widget(Text("Address:", "address"))
    layout.add_widget(Text("Phone number:", "phone"))
    layout.add_widget(Text("Email address:", "email"))
    layout.add_widget(TextBox(5, "Notes:", "notes", as_string=True))

If you want more direct control of your labels, you could use the :py:obj:`.Label` widget to place
them anywhere in the Layout as well as control the justification (left, centre or right) of the text.

Or maybe you just want some static text in your UI?  The simplest thing to do there is to use
the :py:obj:`.Label` widget.  If you need something a little more advanced - e.g. a pre-formatted
multi-line status bar, use a :py:obj:`.TextBox` and disable it as described below.

In some cases, you may want to have different alignments for various blocks of Widgets.  You can use multiple
Layouts in one Frame to handle this case.

For example, if you want a search page, which allows you to enter data at the top and a list of results at the
bottom of the Frame, you could use code like this:

.. code-block:: python

    layout1 = Layout([100])
    frame.add_layout(layout1)
    layout1.add_widget(Text(label="Search:", name="search_string"))

    layout2 = Layout([100])
    frame.add_layout(layout2)
    layout1.add_widget(TextBox(Widget.FILL_FRAME, name="results"))


Disabling widgets
~~~~~~~~~~~~~~~~~
Any widget can be disabled by setting the ``disabled`` property.  When this is ``True``,
asciimatics will redraw the widget using the 'disabled' colour palette entry and prevent the user
from selecting it or editing it.

It is still possible to change the widget programmatically, though.  For example, you can still
change the ``value`` of a disabled widget.

This is the recommended way of getting a piece of non-interactive data (e.g. a status bar) into
your UI.  If the disabled colour is the incorrect choice for your UI, you can override it as
explained in :ref:`custom-colours-ref`.  For an example of such a widget, see the top.py sample.

Layouts in more detail
~~~~~~~~~~~~~~~~~~~~~~
If you need to do something more complex, you can use multiple Layouts.  Asciimatics uses the
following logic to determine the location of Widgets.

1.  The `Frame` owns one or more `Layouts`.  The `Layouts` stack one above each other when
    displayed - i.e. the first `Layout` in the `Frame` is above the second, etc.
2.  Each `Layout` defines some horizontal constraints by defining columns as a proportion of the
    full `Frame` width.
3.  The `Widgets` are assigned a column within the `Layout` that owns them.
4.  The `Layout` then decides the exact size and location to make each `Widget` best fit the
    visible space as constrained by the above.

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

This consists of a single `Frame` with 3 `Layouts`.  The first is a single, full-width column, the
second has two 50% width columns and the third consists of 3 columns of relative size 25:50:25.
The last actually contains some Widgets in the second column (though this is just for illustration
purposes as we'd expect most Layouts to have some Widgets in them).

To get spacing between columns, you can just use a small empty column between your active content.
This size will be proportional to the other columns and so will change as the screen is resized.
If you want to avoid this resizing, you can use the `gutter` option on the `Layout`, which will
always provide an exact character count between columns for all screen sizes.

Filling the space
~~~~~~~~~~~~~~~~~
Once you've got the basic rows and columns for your UI sorted, you may want to use some strategic
spacing.  At the simplest level, you can use the previously mentioned :py:obj:`.Divider` widget to
create some extra vertical space or insert a visual section break.

Moving up the complexity, you can pick different sizes for your Frames based on the size of your
current Screen.  The Frame will be recreated when the screen is resized and so you will use more or
less real estate appropriately.

Finally, you could also tell asciimatics to use an object to fill any remaining space.  This
allows for the sort of UI like you'd see in applications like top where you have a fixed header
or footer, but then a variably sized part that contains the data to be displayed.

You can achieve this in 2 ways:

1. You can tell a Layout to fill any remaining space in the Frame using `fill_frame=True` on
   construction.
2. You can tell some Widgets to fill any remaining space in the Frame using a height of
   `Widget.FILL_FRAME` on construction.

These two methods can be combined to tell a Layout to fill the Frame and a Widget to fill this
Layout.  See the ListView class in the contact_list demo code.

.. warning::

    Note that you can only have one Layout and/or Widget that fills the Frame. Trying to set more
    than one will be rejected.

Full-screen Frames
~~~~~~~~~~~~~~~~~~
By default, asciimatics assumes that you are putting multiple Frames into one Scene and so
provides defaults (e.g. borders) to optimize this type of UI. However, some UIs only need a
single full-screen Frame.  This can easily be achieved by declaring a Frame the full width and
height of the screen and then specifying `has_border=False`.

Large forms
~~~~~~~~~~~
If you have a very large form, you may find it is too big to fit into a standard screen.  This is
not a problem.  You can keep adding your Widgets to your Layout and asciimatics will
automatically clip the content to the space available and scroll the content as required.

If you do this, it is recommended that you set `has_border=True` on the Frame so that the user can
use the scroll bar provided to move around the form.

Colour schemes
~~~~~~~~~~~~~~
The colours for any Widget are determined by the `palette` property of the Frame that contains the
Widget.  If desired, it is possible to have a different palette for every Frame, however your
users may prefer a more consistent approach.

The palette is just a simple dictionary to map Widget components to a colour tuple.  A colour tuple
is simply the foreground colour, attribute and background colour.  For example:

.. code-block:: python

    (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE)

The following table shows the required keys for the `palette`.

========================  =========================================================================
Key                       Usage
========================  =========================================================================
"background"              Frame background
"borders"                 Frame border and Divider Widget
"button"                  Buttons
"control"                 Checkboxes and RadioButtons
"disabled"                Any disabled Widget
"edit_text"               Text and TextBox
"field"                   Value of an option for a Checkbox, RadioButton or Listbox
"focus_button"            Buttons with input focus
"focus_control"           Checkboxes and RadioButtons with input focus
"focus_edit_text"         Text and TextBox with input focus
"focus_field"             As above with input focus
"invalid"                 The widget contains invalid data
"label"                   Widget labels
"scroll"                  Frame scroll bar
"selected_control"        Checkboxes and RadioButtons when selected
"selected_field"          As above when selected
"selected_focus_control"  Checkboxes and RadioButtons with both
"selected_focus_field"    As above with both
"title"                   Frame title
========================  =========================================================================

In addition to the default colour scheme for all your widgets, asciimatics provides some
other pre-defined colour schemes (or themes) that you can use for your widgets using
:py:meth:`~.Frame.set_theme`.  These themes are as follows.

========================  =========================================================================
Name                      Description
========================  =========================================================================
"monochrome"              Simple black and white colour scheme.
"green"                   A classic green terminal.
"bright"                  Black background, green and yellow scheme.
"tlj256"                  Shades of black white and red - 256 colour terminals only.
========================  =========================================================================

You can add your own theme to this list by defining a new entry in the :py:obj:`~.widgets.THEMES`

.. _custom-colours-ref:

Custom widget colours
~~~~~~~~~~~~~~~~~~~~~
In some cases, a single palette for the entire Frame is not sufficient.  If you need a more
fine-grained approach to the colouring, you can customize the colour for any Widget by setting the
:py:obj:`~.Widget.custom_colour` for that Widget.  The only constraint on this property is that
it must still be the value of one of the keys within the owning Frame's palette.

Changing colours inline
~~~~~~~~~~~~~~~~~~~~~~~
The previous options should be enough for most UIs.  However, sometimes it is useful to be able to
change the colour of some text inside the value for some widgets, e.g. to provide syntax highlighting
in a `TextBox`.  You can do this using a :py:obj:`.Parser` object for those widgets that support it.

By passing in a parser that understands extra control codes or the need to highlight certain
characters differently, you can control colours on a letter by letter basis.  Out of the box,
asciimatics provides 2 parsers, which can handle the ${c,a,b} format used by its Renderers, or
the ANSI standard terminal escape codes (used by many Linux terminals).  Simply use the relevant
parser (:py:obj:`~.AsciimaticsParser` or :py:obj:`~.AnsiTerminalParser`) and pass in values containing
the associated control codes to change colours where needed.

Check out the latest code in forms.py and top.py for examples of how this works.

Setting values
--------------
By this stage, you should have a basic User Interface up and running, but how do you set the values
in each of the Widgets - e.g. to pre-populate known values in a form?  There are 2 ways to handle this:

1. You can set the value directly on each `Widget` using the :py:obj:`~.Widget.value` property.
2. You can set the value for all Widgets in a `Frame` by setting at the :py:obj:`~.Frame.data` property.
   This is a simple key/value dictionary, using the `name` property for each `Widget` as the keys.

The latter is a preferred as a symmetrical solution is provided to access all the data for each
Widget, thus giving you a simple way to read and then replay the data back into your Frame.

Getting values
--------------
Now that you have a `Frame` with some `Widgets` in it and the user is filling them in, how do you
find out what they entered?  There are 2 basic ways to do this:

1. You can query each Widget directly, using the `value` property.  This returns the current value
   the user has entered at any time (even when the Frame is not active).  Note that it may be
   `None` for those `Widgets` where there is no value - e.g. buttons.
2. You can query the `Frame`by looking at the `data` property.  This will return the value for
   every Widget in the former as a dictionary, using the Widget `name` properties for the keys.
   Note that `data` is just a cache, which only gets updated when you call :py:meth:`~.Frame.save`,
   so you need to call this method to refresh the cache before accessing it.

For example:

.. code-block:: python

    # Form definition
    layout = Layout([100])
    frame.add_layout(layout)
    layout.add_widget(Text("Name:", "name"))
    layout.add_widget(Text("Address:", "address"))
    layout.add_widget(TextBox(5, "Notes:", "notes", as_string=True))

    # Sample frame.data after user has filled it in.
    {
        "name": "Peter",
        "address": "Somewhere on earth",
        "notes": "Some multi-line\ntext from the user."
    }

Validating text data
~~~~~~~~~~~~~~~~~~~~
Free-form text input sometimes needs validating to make sure that the user has entered the right
thing - e.g. a valid email address - in a form.  Asciimatics makes this easy by adding the
`validator` parameter to `Text` widgets.

This parameter takes either a regular expression string or a function (taking a single parameter
of the current widget value).  Asciimatics will use it to determine if the widget contains valid
data.  It uses this information in 2 places.

1. Whenever the `Frame` is redrawn, asciimatics will check the state and flag any invalid values
   using the `invalid` colour palette selection.

2. When your program calls :py:meth:`~.Frame.save` specifying `validate=True`, asciimatics will
   check all fields and throw an :py:obj:`.InvalidFields` exception if it finds any invalid data.

Input focus
~~~~~~~~~~~
As mentioned in the explanation of colour palettes, asciimatics has the concept of an input focus.
This is the Widget that will take any input from the keyboard.  Assuming you are using the
default palette, the Widget with the input focus will be highlighted.  You can move the focus
using the cursor keys, tab/backtab or by using the mouse.

The exact way that the mouse affects the focus depends on a combination of the capabilities of
your terminal/console and the settings of your Frame.  At a minimum, clicking on the Widget will
always work.  If you specify `hover_focus=True` and your terminal supports reporting mouse move
events, just hovering over the Widget with the mouse pointer will move the focus.

Modal Frames
~~~~~~~~~~~~
When constructing a Frame, you can specify whether it is modal or not using the `is_modal`
parameter.  Modal Frames will not allow any input to filter through to other Effects in the Scene,
so when one is on top of all other Effects, this means that only it will see the user input.

This is commonly used for, but not limited to, notifications to the user that must be acknowledged
(as implemented by :py:obj:`.PopUpDialog`).

Global key handling
~~~~~~~~~~~~~~~~~~~
In addition to mouse control to switch focus, you can also set up a global event handler to
navigate your forms.  This is useful for keyboard shortcuts - e.g. Ctrl+Q to quit your program.

To set up this handler, you need to pass it into your screen on the `play()` Method.  For example

.. code-block:: python

    # Event handler for global keys
    def global_shortcuts(event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            # Stop on ctrl+q or ctrl+x
            if c in (17, 24):
                raise StopApplication("User terminated app")

    # Pass this to the screen...
    screen.play(scenes, unhandled_input=global_shortcuts)

.. warning::

    Note that the global handler is only called if the focus does not process the event.  Some
    widgets - e.g. TextBox - take any printable text and so the only keys that always get to this
    handler are the control codes.  Others will sometimes get here depending on the type of Widget
    in focus and whether the Frame is modal or not..

By default, the global handler will do nothing if you are playing any Scenes containing a Frame.
Otherwise it contains the top-level logic for skipping to the next Scene (on space or enter), or
exiting the program (on Q or X).

Dealing with Ctrl+C and Ctrl+Z
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A lot of modern UIs want to be able to use Ctrl+C/Z to do something other than kill the
application.  The problem for Python is that this normally triggers a `KeyboardInterrupt` - which
typically kills the application - or causes the operating system to suspend the process (on UNIX
variants).

If you want to prevent this and use Ctrl+C/Z for another purpose, you can tell asciimatics to
catch the low-level signals to prevent these interrupts from being generated (and so return the
keypress to your application).  This is done by specifying `catch_interrupt=True` when you create
the `Screen` by calling :py:meth:`.wrapper`.

Dealing with Ctrl+S
~~~~~~~~~~~~~~~~~~~
Back in the days when terminals really were separate machines connected over wires to a computer,
it was necessary to be able to signal that the terminal needed time to catch up.  This was done
using software flow control, using the Ctrl+S/Ctrl+Q control codes to tell the computer to
stop/restart sending text.

These days, it's not really necessary, but is still a supported feature on most terminals.  On
some systems you can switch this off so you get access to Ctrl+S, but it is not possible on them
all.  See :ref:`ctrl-s-issues-ref` for details
on how to fix this.

Flow of control
---------------
By this stage you should have a program with some Frames and can extract what your user has
entered into any of them.  But how do you know when to act and move between Frames?  The answer
is callbacks and exceptions.

Callbacks
~~~~~~~~~
A callback is just a function that you pass into another function to be called when the
associated event occurs.  In asciimatics, they can usually be identified by the fact that they
start with `on` and correspond to a significant input action from the user, e.g. `on_click`.

When writing your application, you simply need to decide which events you want to use to trigger
some processing and create appropriate callbacks.  The most common pattern is to use a `Button` and
define an `on_click` callback.

In addition, there are other events that can be triggered when widget values change.  These can
be used to provide dynamic effects like enabling/disabling Buttons based on the current value of
another Widget.

Exceptions
~~~~~~~~~~
Asciimatics uses exceptions to tell the animation engine to move to a new Scene or stop the whole
 process.  Other exceptions are not caught and so can still be used as normal.  The details for
 the new exceptions are as follows:

1. :py:obj:`.StopApplication` - This exception will stop the animation engine and return flow to
   the function that called into the Screen.
2. :py:obj:`.NextScene` - This exception tells the animation engine to move to a new Scene.  The
   precise Scene is determined by the name passed into the exception.  If none is specified, the
   engine will simply round robin to the next available Scene.

Note that the above logic requires each Scene to be given a unique name on construction.  For
example:

.. code-block:: python

    # Given this scene list...
    scenes = [
        Scene([ListView(screen, contacts)], -1, name="Main"),
        Scene([ContactView(screen, contacts)], -1, name="Edit Contact")
    ]
    screen.play(scenes)

    # You can use this code to move back to the first scene at any time...
    raise NextScene("Main")

Data handling
-------------
By this stage you should have everything you need for a fully functional UI.  However, it may not be quite
clear how to pass data around all your component parts because asciimatics doesn't provide any classes to do
it for you.  Why?  Because we don't want to tie you down to a specific implementation.  You should be able to
pick your own!

Look back at the earlier explanation of model/view design.  The model can be any class you like!  All you
need to do is:

1. Define a model class to store any state and provide suitable APIs to access it as needed from your UI
   (a.k.a. views).
2. Define your own views (based on an ``Effect`` or ``Frame``) to define your UI and store a reference to the
   model (typically as a parameter on construction).
3. Use that saved reference to the model to handle updates as needed inside your view's callbacks or methods.

For a concrete example of how to do this check out the contact list sample and look at how it defines and uses
the ``ContactModel``.  Alternatively, the quick_model sample shows how the same forms would work with a simple
list of dictionaries instead.

Dynamic scenes
--------------
That done, there are just a few more final touches to consider.  These all touch on dynamically changing or
reconstructing your Scene.

At a high level, you need to decide what you want to achieve.  The basic options are as follows.

1. If you just want to have some extra Frames on the same Screen - e.g. pop-up windows - that's
   fine.  Just use the existing classes (see below)!
2. If you want to be able to draw other content outside of your existing Frame(s), you probably
   want to use other Effects.
3. If you want to be able to add something inside your Frame(s), you almost certainly want to
   create a custom Widget for that new content.

The rest of this section goes through those options (and a couple more related changes) in a
little more detail.

Adding other effects
~~~~~~~~~~~~~~~~~~~~
Since Frames are just another Effect, they can be combined with any other Effect in a Scene.  For
example, this will put a simple input form over the top of the animated Julia set Effect:

.. code-block:: python

    scenes = []
    effects = [
        Julia(screen),
        InputFormFrame(screen)
    ]
    scenes.append(Scene(effects, -1))
    screen.play(scenes)

The ordering is important.  The effects at the bottom of the list are at the top of the screen Z
order and so will be displayed in preference to those lower in the Z order (i.e. those earlier in
the list).

The most likely reason you will want to use this is to use the :py:obj:`.Background` Effect to
set a background colour for the whole screen behind your Frames.  See the forms.py demo for an
example of this use case.

Pop-up dialogs
~~~~~~~~~~~~~~
Along a similar line, you can also add a :py:obj:`.PopUpDialog` to your Scenes at any time.  These
consist of a single text message and a set of buttons that you can define when creating the dialog.

Owing to restrictions on how objects need to be rebuilt when the screen is resized, these should be
limited to simple are confirmation or error cases - e.g. "Are you sure you want to quit?"  For more
details on the restrictions, see the section on restoring state.

Pop-up menus
~~~~~~~~~~~~
You can also add a :py:obj:`.PopupMenu` to your Scenes in the same way.  These allow you to create a
simple temporary list of options from which the user has to select just one entry (by clicking on it
or moving the focus and pressing Enter) or dismiss the whole list (by pressing Escape or clicking
outside of the menu).

Owing to their temporary nature, they are not maintained over screen resizing.

Event handling with multiple Frames
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In order to work similarly to a GUI desktop, Frames check if they are at the front of the Z order.
if one determines that it is at the front, it will swallow all keyboard events that it receives.
This prevents keys from randomly triggering effects in lower windows (which would be unexpected in
a desktop environment).  As a result, there will never be unhandled keyboard input for a Scene that
contains any Frames.

Mouse events may still be passed to the unhandled input handler if they fall outside of all Effects
on the Screen.

Screen resizing
~~~~~~~~~~~~~~~
If you follow the standard application mainline logic as found in all the sample code, your
application will want to resize all your Effects and Widgets whenever the user resizes the
terminal.  To do this you need to get a new Screen then rebuild a new set of objects to use that
Screen.

Sound like a bit of a drag, huh?  This is why it is recommended that you separate your
presentation from the rest of your application logic.  If you do it right you will find that it
actually just means you go through exactly the same initialization path as you did before to
create your Scenes in the first place.  There are a couple of gotchas, though.

First, you need to make sure that asciimatics will exit and recreate a new Screen when the
terminal is resized.  You do that with this boilerplate code that is in most of the samples.

.. code-block:: python

    def main(screen, scene):
        # Define your Scenes here
        scenes = ...

        # Run your program
        screen.play(scenes, stop_on_resize=True, start_scene=scene)

    last_scene = None
    while True:
        try:
            Screen.wrapper(main, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene

This will allow you to decide how all your UI should look whenever the screen is resized and will
 restart at the Scene that was playing at the time of the resizing.

Restoring state
~~~~~~~~~~~~~~~
Recreating your view is only half the story.  Now you need to ensure that you have restored any
state inside your application - e.g. any dynamic effects are added back in, your new Scene has
the same internal state as the old, etc. Asciimatics provides a standard interface (the `clone`
method) to help you out here.

When the running `Scene` is resized (and passed back into the Screen as the start scene), the new
`Scene` will run through all the `Effects` in the old copy looking for any with a `clone` method.
If it finds one, it will call it with 2 parameters: the new `Screen` and the new `Scene` to own the
cloned `Effect`.  This allows you to take full control of how the new `Effect` is recreated.
Asciimatics uses this interface in 2 ways by default:

1.  To ensure that any :py:obj:`~.Frame.data` is restored in the new `Scene`.
2.  To duplicate any dynamically added :py:obj:`.PopUpDialog` objects in the new `Scene`.

You could override this processing to handle your own custom cloning logic.  The formal definition
of the API is defined as follows.

.. code-block:: python

    def clone(self, screen, scene):
        """
        Create a clone of this Effect into a new Screen.

        :param screen: The new Screen object to clone into.
        :param scene: The new Scene object to clone into.
        """

Reducing CPU usage
~~~~~~~~~~~~~~~~~~
It is the nature of text UIs that they don't need to refresh anywhere near as often as a full-blown
animated Scene.  Asciimatics therefore optimizes the refresh rate when only Frames are being
displayed on the Screen.

However, there are some widgets that can reduce the need for animation even further by not
requesting animation updates (e.g. for a blinking cursor).  If this is an issue for your
application, you can specify ``reduce_cpu=True`` when constructing your Frames.  See
contact_list.py for an example of this.

Custom widgets
--------------
To develop your own widget, you need to define a new class that inherits from :py:obj:`.Widget`.
You then have to implement the following functions.

1. :py:meth:`~.Widget.reset` - This is where you should reset any state for your widget.  It gets
   called whenever the owning Frame is initialised, which can be when it is first displayed, when
   the user moves to a new Scene or when the screen is resized.
2. :py:meth:`~.Widget.update` - This is where you should put the logic to draw your widget.  It
   gets called every time asciimatics needs to redraw the screen (and so should always draw the
   entire widget).
3. :py:meth:`~.Widget.process_event` - This is where you should put your code to handle mouse and
   keyboard events.
4. :py:obj:`~.Widget.value` - This must return the current value for the widget.
5. :py:meth:`~.Widget.required_height` - This returns the minimum required height for your widget.
   It is used by the owning Layout to determine the size and location of your widget.

With these all defined, you should now be able to add your new custom widget to a Layout like any
of the standard ones delivered in this package.
