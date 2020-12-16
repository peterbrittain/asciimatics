# -*- coding: utf-8 -*-
"""This module defines a file browser selection"""
from re import compile as re_compile
import os
import unicodedata
from collections import namedtuple
from asciimatics.utilities import readable_timestamp, readable_mem
from asciimatics.widgets.multicolumnlistbox import MultiColumnListBox

class FileBrowser(MultiColumnListBox):
    """
    A FileBrowser is a widget for finding a file on the local disk.
    """

    def __init__(self, height, root, name=None, on_select=None, on_change=None, file_filter=None):
        r"""
        :param height: The desired height for this widget.
        :param root: The starting root directory to display in the widget.
        :param name: The name of this widget.
        :param on_select: Optional function that gets called when user selects a file (by pressing
            enter or double-clicking).
        :param on_change: Optional function that gets called on any movement of the selection.
        :param file_filter: Optional RegEx string that can be passed in to filter the files to be displayed.

        Most people will want to use a filter to finx files with a particular extension.  In this case,
        you must use a regex that matches to the end of the line - e.g. use ".*\.txt$" to find files ending
        with ".txt".  This ensures that you don't accidentally pick up files containing the filter.
        """
        super(FileBrowser, self).__init__(
            height,
            [0, ">8", ">14"],
            [],
            titles=["Filename", "Size", "Last modified"],
            name=name,
            on_select=self._on_selection,
            on_change=on_change)

        # Remember the on_select handler for external notification.  This allows us to wrap the
        # normal on_select notification with a function that will open new sub-directories as
        # needed.
        self._external_notification = on_select
        self._root = root
        self._in_update = False
        self._initialized = False
        self._file_filter = None if file_filter is None else re_compile(file_filter)

    def update(self, frame_no):
        # Defer initial population until we first display the widget in order to avoid race
        # conditions in the Frame that may be using this widget.
        if not self._initialized:
            self._populate_list(self._root)
            self._initialized = True
        super(FileBrowser, self).update(frame_no)

    def _on_selection(self):
        """
        Internal function to handle directory traversal or bubble notifications up to user of the
        Widget as needed.
        """
        if self.value and os.path.isdir(self.value):
            self._populate_list(self.value)
        elif self._external_notification:
            self._external_notification()

    def clone(self, new_widget):
        # Copy the data into the new widget.  Notes:
        # 1) I don't really want to expose these methods, so am living with the protected access.
        # 2) I need to populate the list and then assign the values to ensure that we get the
        #    right selection on re-sizing.
        new_widget._populate_list(self._root)
        new_widget._start_line = self._start_line
        new_widget._root = self._root
        new_widget.value = self.value

    def _populate_list(self, value):
        """
        Populate the current multi-column list with the contents of the selected directory.

        :param value: The new value to use.
        """
        # Nothing to do if the value is rubbish.
        if value is None:
            return

        # Stop any recursion - no more returns from here to end of fn please!
        if self._in_update:
            return
        self._in_update = True

        # We need to update the tree view.
        self._root = os.path.abspath(value if os.path.isdir(value) else os.path.dirname(value))

        # The absolute expansion of "/" or "\" is the root of the disk, so is a cross-platform
        # way of spotting when to insert ".." or not.
        tree_view = []
        if len(self._root) > len(os.path.abspath(os.sep)):
            tree_view.append((["|-+ .."], os.path.abspath(os.path.join(self._root, ".."))))

        tree_dirs = []
        tree_files = []
        try:
            files = os.listdir(self._root)
        except OSError:
            # Can fail on Windows due to access permissions
            files = []
        for my_file in files:
            full_path = os.path.join(self._root, my_file)
            try:
                details = os.lstat(full_path)
            except OSError:
                # Can happen on Windows due to access permissions
                details = namedtuple("stat_type", "st_size st_mtime")
                details.st_size = 0
                details.st_mtime = 0
            name = "|-- {}".format(my_file)
            tree = tree_files
            if os.path.isdir(full_path):
                tree = tree_dirs
                if os.path.islink(full_path):
                    # Show links separately for directories
                    real_path = os.path.realpath(full_path)
                    name = "|-+ {} -> {}".format(my_file, real_path)
                else:
                    name = "|-+ {}".format(my_file)
            elif self._file_filter and not self._file_filter.match(my_file):
                # Skip files that don't match the filter (if present)
                continue
            elif os.path.islink(full_path):
                # Check if link target exists and if it does, show statistics of the
                # linked file, otherwise just display the link
                try:
                    real_path = os.path.realpath(full_path)
                except OSError:
                    # Can fail on Linux prof file system.
                    real_path = None
                if real_path and os.path.exists(real_path):
                    details = os.stat(real_path)
                    name = "|-- {} -> {}".format(my_file, real_path)
                else:
                    # Both broken directory and file links fall to this case.
                    # Actually using the files will cause a FileNotFound exception
                    name = "|-- {} -> {}".format(my_file, real_path)

            # Normalize names for MacOS and then add to the list.
            tree.append(([unicodedata.normalize("NFC", name),
                          readable_mem(details.st_size),
                          readable_timestamp(details.st_mtime)], full_path))

        tree_view.extend(sorted(tree_dirs))
        tree_view.extend(sorted(tree_files))

        self.options = tree_view
        self._titles[0] = self._root

        # We're out of the function - unset recursion flag.
        self._in_update = False
