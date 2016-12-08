import ftplib
import re

import wxversion
wxversion.select("3.0")
import wx

import Images

COMPUTER = 0
FOLDER = 1
GENERIC_FILE = 2
VLC = 3
ZIP = 4
EXE = 5
IMAGE = 6
MUSIC = 7
PDF = 8
RAR = 9
ISO = 10
SPREADSHEET = 11
TEXT = 12
TORRENT = 13
file_to_icon = {'mp4': VLC,
                'avi': VLC,
                'mkv': VLC,
                'zip': ZIP,
                'exe': EXE,
                'jpg': IMAGE,
                'mp3': MUSIC,
                'wav': MUSIC,
                'flac': MUSIC,
                'pdf': PDF,
                'rar': RAR,
                'iso': ISO,
                'xls': SPREADSHEET,
                'xlsx': SPREADSHEET,
                'csv': SPREADSHEET,
                'txt': TEXT,
                'torrent': TORRENT}


class FTPExplorePanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent
        #self.ftp_crawler = FTPCrawler()
        self.directory_tree = None
        self.ftp_log = None
        self.ftp_connection = None
        self.init_ui()

        #self.open_connection('73.207.63.191')

    def init_ui(self):
        image_list = wx.ImageList(16, 16)
        for image in Images.icon_list:
            image_list.Add(image.GetBitmap())

        main_vsizer = wx.BoxSizer(wx.VERTICAL)

        ftp_connection_label = wx.StaticText(parent=self, label='FTP Connection:')

        splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_BORDER)
        self.directory_tree = wx.TreeCtrl(parent=splitter)
        self.directory_tree.AssignImageList(image_list)
        self.directory_tree.Bind(event=wx.EVT_TREE_ITEM_EXPANDING, handler=self.directory_expanded_callback)

        self.ftp_log = wx.TextCtrl(parent=splitter, style=wx.TE_MULTILINE)

        splitter.SetMinimumPaneSize(100)
        splitter.SplitHorizontally(self.directory_tree, self.ftp_log)
        main_vsizer.Add(ftp_connection_label, flag=wx.RIGHT | wx.UP | wx.DOWN, border=5)
        main_vsizer.Add(splitter, flag=wx.EXPAND | wx.RIGHT | wx.DOWN, proportion=1, border=5)

        self.SetSizer(main_vsizer)

    def log(self, message):
        self.ftp_log.AppendText(message + '\n')

    def get_item_path(self, item):
        path = '/{}'.format(self.directory_tree.GetItemText(item))

        root = self.directory_tree.GetRootItem()
        parent = self.directory_tree.GetItemParent(item)
        while parent != root and parent.IsOk():
            path = '{}/{}'.format(self.directory_tree.GetItemText(parent), path)
            parent = self.directory_tree.GetItemParent(parent)

        return path

    def directory_expanded_callback(self, event):
        item = event.GetItem()
        if item == self.directory_tree.GetRootItem():
            return
        path = self.get_item_path(event.GetItem())
        self.directory_tree.DeleteChildren(item)
        self.append_directory_to_item(path, event.GetItem())

    def append_directory_to_item(self, directory, item):
        dir_list = []
        self.log('Retrieving directory listing: {}'.format(directory))
        self.ftp_connection.dir(directory, dir_list.append)

        for listing in dir_list:
            dir_listing_pattern = '^(?P<dir>[\-ld])(?P<permissions>([\-r][\-w][\-xs]){3})\s+(\d+)\s+(\w+)\s+(\w+)' \
                                  '\s+(\d+)\s+(((\w{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+' \
                                  '(\d{4})))\s+(?P<name>.+)$'
            match_obj = re.match(dir_listing_pattern, listing)
            if match_obj:
                match_group_dict = match_obj.groupdict()
            is_dir = (match_group_dict['dir'] == 'd')
            item_name = match_group_dict['name']
            if is_dir:
                image_index = FOLDER
            else:
                extension = item_name[-3:].lower()
                image_index = file_to_icon.get(extension, GENERIC_FILE)
            current_item = self.directory_tree.AppendItem(parent=item, text=item_name, image=image_index)
            if is_dir:
                self.directory_tree.AppendItem(parent=current_item, text='dummy')

    def open_connection(self, ip):
        if self.ftp_connection:
            self.ftp_connection.close()
        self.directory_tree.DeleteAllItems()
        try:
            self.log("Connecting to: {}".format(ip))
            self.ftp_connection = ftplib.FTP(ip, timeout=10)
            self.ftp_connection.login()
            self.log("Connection Successful")
            self.ftp_connection.sendcmd('TYPE i')
            root = self.directory_tree.AddRoot(text=ip, image=COMPUTER)
            self.append_directory_to_item('/', self.directory_tree.GetRootItem())
            self.directory_tree.Expand(root)

        except ftplib.socket.error as e:
            message = 'Connection to {} failed: {}'.format(ip, e)
            self.log(message)
