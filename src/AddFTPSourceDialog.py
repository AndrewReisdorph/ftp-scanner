# Builtins
import re

# wxpython
import wx


class AddFTPSourceDialog(wx.Dialog):

    def __init__(self, parent):
        super(AddFTPSourceDialog, self).__init__(parent=parent, style=wx.CAPTION | wx.CLOSE_BOX | wx.SYSTEM_MENU,
                                                 title='Add Source')
        self.parent = parent
        self.ip = None
        self.path = None
        self.canceled = True

        self.ip_textctrl = None
        self.path_textctrl = None

        self.init_ui()

    def init_ui(self):
        ip_label = wx.StaticText(parent=self, label='IP:')
        self.ip_textctrl = wx.TextCtrl(parent=self)

        path_label = wx.StaticText(parent=self, label='Path:')
        self.path_textctrl = wx.TextCtrl(parent=self, value='/')

        add_source_button = wx.Button(parent=self, label='Add Source')
        add_source_button.Bind(wx.EVT_BUTTON, handler=self.add_source_button_callback)
        cancel_button = wx.Button(parent=self, label='Cancel')
        cancel_button.Bind(wx.EVT_BUTTON, handler=self.cancel_button_callback)

        ip_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        path_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        button_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        main_vsizer = wx.BoxSizer(wx.VERTICAL)
        ip_hsizer.Add(ip_label, flag=wx.RIGHT, border=5)
        ip_hsizer.Add(self.ip_textctrl, flag=wx.EXPAND, proportion=1)

        path_hsizer.Add(path_label, flag=wx.RIGHT, border=5)
        path_hsizer.Add(self.path_textctrl, flag=wx.EXPAND, proportion=1)

        button_hsizer.Add(add_source_button, flag=wx.RIGHT, border=5)
        button_hsizer.Add(cancel_button)

        main_vsizer.Add(ip_hsizer, flag=wx.ALL | wx.EXPAND, border=5)
        main_vsizer.Add(path_hsizer, flag=wx.LEFT | wx.RIGHT | wx.DOWN | wx.EXPAND, border=5)
        main_vsizer.Add(button_hsizer, flag=wx.LEFT | wx.RIGHT | wx.DOWN, border=5)

        self.SetSizer(main_vsizer)
        main_vsizer.Fit(self)

    def cancel_button_callback(self, event):
        event.Skip()
        self.Destroy()

    def add_source_button_callback(self, event):
        event.Skip()

        ip_text = self.ip_textctrl.GetLineText(0)
        path_text = self.path_textctrl.GetLineText(0)

        warning_message = None
        if ip_text == '':
            warning_message = 'No IP entered.'
        elif not re.match(r'^(\d{1,3}.){3}\d{1,3}$', ip_text):
            warning_message = 'Entered invalid IP'
        if warning_message:
            wx.MessageDialog(parent=self, message=warning_message).ShowModal()
            return

        self.ip = ip_text
        self.path = path_text
        self.canceled = False
        self.Destroy()