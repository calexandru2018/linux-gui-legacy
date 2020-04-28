class DialogHandler: 
    def __init__(self, interface): 

        # Should also be passed
        self.interface = interface
        # self.messagedialog_window = self.interface.get_object("MessageDialog")
        # self.messagedialog_label = self.interface.get_object("message_dialog_label")
        # self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        # self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        # self.messagedialog_sub_label.hide()

        # # Settings related
        # self.update_killswitch_switch = self.interface.get_object("update_killswitch_switch")
        # self.split_tunneling_switch = self.interface.get_object("split_tunneling_switch")
        # self.settings_tab_dict = {
        #     "general_tab_style": self.interface.get_object("general_tab_label").get_style_context(), 
        #     "sys_tray_tab_style": self.interface.get_object("sys_tray_tab_label").get_style_context(),
        #     "connection_tab_style": self.interface.get_object("connection_tab_label").get_style_context(),
        #     "advanced_tab_style": self.interface.get_object("advanced_tab_label").get_style_context()
        # }

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
