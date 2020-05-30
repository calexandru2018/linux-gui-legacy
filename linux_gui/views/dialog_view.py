from threading import Thread

from ..gui_logger import gui_logger
from ..constants import (
    UI_DIALOG, 
)

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

class DialogView: 
    def __init__(self, interface, Gtk, queue):
        interface.add_from_file(UI_DIALOG)
        interface.connect_signals({
            "close_message_dialog": self.close_message_dialog,
            "MessageDialog_delete_event": self.MessageDialog_delete_event,
        })

        self.messagedialog_window = interface.get_object("MessageDialog")
        self.messagedialog_label = interface.get_object("message_dialog_label")
        self.messagedialog_spinner = interface.get_object("message_dialog_spinner")
        self.messagedialog_sub_label = interface.get_object("message_dialog_sub_label")
        self.messagedialog_sub_label.hide()

        self.message_dialog_close_button = interface.get_object("message_dialog_close_button")

        self.interface = interface 
        self.gtk = Gtk
        self.queue = queue

        thread = Thread(target=self.listener)
        thread.daemon = True
        thread.start()

    def listener(self):
        while True:
            kwargs = self.queue.get()

            try:
                if "display_dialog" in kwargs.get("action"):
                    # self.display_dialog(**kwargs)
                    gobject.idle_add(self.display_dialog, kwargs)
                    self.queue.task_done()
                if "update_dialog" in kwargs.get("action"):
                    # self.update_dialog(**kwargs)
                    gobject.idle_add(self.update_dialog, kwargs)
                    self.queue.task_done()

                if "hide_dialog" in kwargs.get("action"):
                    # self.hide_dialog()
                    gobject.idle_add(self.hide_dialog)
                    self.queue.task_done()
                    
                if "hide_spinner" in kwargs.get("action"):
                    # self.hide_spinner()
                    gobject.idle_add(self.hide_spinner)
                    self.queue.task_done()
            except TypeError:
                gui_logger.debug(">>> Error occurs due to testing.") 

    def display_dialog(self, kwargs):
        self.message_dialog_close_button.show()
        self.messagedialog_sub_label.hide()
        self.messagedialog_spinner.hide()

        if "label" in kwargs:
            self.messagedialog_label.set_markup(kwargs.get("label")) 

        if "spinner" in kwargs and kwargs.get("spinner"):
            self.messagedialog_spinner.show()

        if "sub_label" in kwargs and kwargs.get("sub_label"):
            self.messagedialog_sub_label.set_markup(kwargs.get("sub_label"))
            self.messagedialog_sub_label.show()

        if "hide_close_button" in kwargs and kwargs.get("hide_close_button"):
            self.message_dialog_close_button.hide()
            self.messagedialog_window.connect("destroy", self.gtk.main_quit)
        
        self.messagedialog_window.show()

    def update_dialog(self, kwargs):
        self.message_dialog_close_button.show()
        self.messagedialog_sub_label.hide()
        self.messagedialog_spinner.hide()

        if "label" in kwargs:
            self.messagedialog_label.set_markup(kwargs.get("label")) 

        if "spinner" in kwargs and kwargs.get("spinner"):
            self.messagedialog_spinner.show()

        if "sub_label" in kwargs and kwargs.get("sub_label"):
            self.messagedialog_sub_label.set_markup(kwargs.get("sub_label"))
            self.messagedialog_sub_label.show()

        if "hide_close_button" in kwargs and kwargs.get("hide_close_button"):
            self.message_dialog_close_button.hide()
            self.messagedialog_window.connect("destroy", self.gtk.main_quit)            

    def hide_spinner(self):
        self.messagedialog_spinner.hide()

    def hide_dialog(self):
        self.messagedialog_window.hide()

    def close_message_dialog(self, button):
        """Button/Event handler to close message dialog.
        """
        self.interface.get_object("MessageDialog").hide()
        
    # To avoid getting the MessageDialog destroyed and not being re-rendered again
    def MessageDialog_delete_event(self, window, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if window.get_property("visible") is True:
            window.hide()
            return True
