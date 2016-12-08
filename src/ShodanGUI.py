import wxversion
wxversion.select("3.0")
import wx

import Images
import FTPExplorePanel
import ShodanExplorer


class ResultsPanel(wx.Panel):

    def __init__(self, parent, main_app):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.main_app = main_app
        self.list = None
        self.init_ui()

    def init_ui(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        results_label = wx.StaticText(parent=self, label='Results')
        self.list = wx.ListBox(parent=self)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, handler=self.result_double_click_callback)
        main_sizer.Add(results_label, flag=wx.ALL, border=5)
        main_sizer.Add(self.list, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.DOWN, border=5)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)

        self.list.InsertItems(['73.207.63.191', '104.13.194.249'], 0)

    def result_double_click_callback(self, event):
        self.main_app.ftp_connect(event.GetString())
        print event.GetString()

    def append(self, results_list, clear_list=False):
        if clear_list:
            self.list.Clear()
        self.list.InsertItems(results_list, 0)


class ToolbarPanel(wx.Panel):

    def __init__(self, parent, main_app):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        self.main_app = main_app
        self.init_ui()

    def init_ui(self):
        main_hsizer = wx.BoxSizer(wx.HORIZONTAL)

        query_textctrl = wx.SearchCtrl(parent=self, style=wx.TE_PROCESS_ENTER)
        query_textctrl.Bind(wx.EVT_TEXT_ENTER, handler=self.on_query_enter)
        scan_button = wx.BitmapButton(parent=self, bitmap=Images.scan_16.GetBitmap())

        main_hsizer.Add(query_textctrl, flag=wx.ALL | wx.EXPAND, border=5, proportion=1)
        main_hsizer.Add(scan_button, flag=wx.UP | wx.RIGHT, border=5)
        self.SetSizer(main_hsizer)

    def on_query_enter(self, event):
        self.main_app.do_query(event.GetString())


class ShodanGUI(wx.Frame):

    def __init__(self, parent):
        super(ShodanGUI, self).__init__(parent, title='Shodan Explorer', size=(800, 800))
        self.parent = parent
        self.shodan_explorer = ShodanExplorer.ShodanExplorer()
        self.ftp_explore_panel = None
        self.results_panel = None
        self.shodan_explorer.login()

    def init_gui(self):
        main_vsizer = wx.BoxSizer(wx.VERTICAL)

        toolbar_panel = ToolbarPanel(self, self)
        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_BORDER)
        splitter.SetMinimumPaneSize(100)
        self.results_panel = ResultsPanel(parent=splitter, main_app=self)
        self.ftp_explore_panel = FTPExplorePanel.FTPExplorePanel(parent=splitter)
        splitter.SplitVertically(self.results_panel, self.ftp_explore_panel)

        main_vsizer.Add(toolbar_panel, flag=wx.EXPAND)
        main_vsizer.Add(splitter, proportion=1, flag=wx.EXPAND)
        self.SetSizer(main_vsizer)

    def ftp_connect(self, ip):
        self.ftp_explore_panel.open_connection(ip)

    def do_query(self, query):
        results = self.shodan_explorer.get_query_results(query)
        self.results_panel.append(results, True)


if __name__ == '__main__':
    app = wx.App()
    main_frame = ShodanGUI(None)
    main_frame.Show()
    app.MainLoop()
