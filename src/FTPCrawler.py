import time
import re
import ftplib
import guessit

import wxversion
wxversion.select( "3.0" )
import wx

from VideoInfoFinder import VideoInfoFinder

# hello
class FTPCrawler(object):

    def __init__(self, ip_address, search_path, main_app):
        self.ip_address = ip_address
        self.search_path = search_path
        self.main_app = main_app
        self.connection = None
        self.directory_tree = {'/': {}}
        self.video_info_finder = VideoInfoFinder()

    def connect(self):
        try:
            self.connection = ftplib.FTP(self.ip_address, timeout=30)
            self.connection.login()
            self.connection.sendcmd('TYPE i')
        except:
            print "Connection failed."
            return False
        print "Connection established."
        return True

    def close(self):
        self.connection.close()

    def append_directory_tree(self, path, item, is_file):
        #print 'appending {} to {}'.format(item, path)
        if path == '/':
            self.directory_tree[path][item] = {}
        else:
            parent_node = self.directory_tree['/']
            for directory in path.split('/'):
                if directory == '':
                    continue
                else:
                    if directory not in parent_node:
                        parent_node[directory] = {}
                    parent_node = parent_node[directory]
            if is_file:
                parent_node[item] = None
            else:
                parent_node[item] = {}

    def sizeof_fmt(self, num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def scan(self, directory=None):
        if self.main_app.quit_request:
            return
        #print "Scan received directory: {}".format(directory)
        if directory is None:
            directory = self.search_path
            #directory = self.connection.pwd()

        dir_list = []
        self.connection.dir(directory, dir_list.append)

        for item in dir_list:
            #print item
            #groups = re.match(r'(d|-)[rwx-]{9}\s+\d+\s+[a-z]+\s+[a-z]+\s+\d+\s+[A-Z][a-z]+\s+\d+\s+(\d+:\d+|\d{4})\s(.*)',item).groups()
            groups = re.match(r'^([\-ld])(([\-r][\-w][\-xs]){3})\s+(\d+)\s+(\w+)\s+(\w+)\s+(\d+)\s+(((\w{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+(\d{4})))\s+(.+)$',item).groups()
            is_dir = (groups[0] == 'd')
            item_name = groups[-1]

            if is_dir:
                self.append_directory_tree(directory[1:], item_name, False)
                self.scan('{}/{}'.format(directory, item_name))
            else:
                self.connection.sendcmd("TYPE i")
                extension = item_name[-4:]
                if extension in ['.avi', '.mkv', '.mp4']:
                    if 'sample' not in item_name and 'Sample' not in item_name:
                        parent_directory = directory.split('/')[-1]
                        video_info = self.video_info_finder.get_video_info(item_name[:-4],parent_directory)
                        video_info['filename'] = item_name
                        video_info['ip'] = self.ip_address
                        video_info['filesize'] = self.sizeof_fmt(self.connection.size(directory+'/'+item_name))
                        video_info['parent_dir'] = parent_directory
                        wx.CallAfter(self.main_app.process_new_result, result_dict=video_info)
                        #self.result_queue.put(guessit_dict)
                self.append_directory_tree(directory, item_name, True)
