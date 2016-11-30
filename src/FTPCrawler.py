import re
import ftplib

import wxversion
wxversion.select("3.0")
import wx

import VideoInfoFinder

class FTPCrawler(object):

    def __init__(self, ip_address, search_path, main_app):
        self.ip_address = ip_address
        self.search_path = search_path
        self.main_app = main_app
        self.connection = None
        self.directory_tree = {'/': {}}
        self.video_info_finder = VideoInfoFinder.VideoInfoFinder()

    def connect(self):
        try:
            self.connection = ftplib.FTP(self.ip_address, timeout=30)
            self.connection.login()
            self.connection.sendcmd('TYPE i')
        except ftplib.socket.error as e:
            self.log("Connection failed: {}".format(e))
            return False
        self.log("Connection established.")
        return True

    def close(self):
        self.connection.close()

    def append_directory_tree(self, path, item, is_file):
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

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Yi', suffix)

    def log(self, message):
        self.main_app.log(message)

    def scan(self, directory=None):
        if self.main_app.quit_request:
            return

        if directory is None:
            directory = self.search_path

        dir_list = []
        self.connection.dir(directory, dir_list.append)

        for item in dir_list:
            dir_listing_pattern = '^(?P<dir>[\-ld])(?P<permissions>([\-r][\-w][\-xs]){3})\s+(\d+)\s+(\w+)\s+(\w+)' \
                                  '\s+(\d+)\s+(((\w{3})\s+(\d{1,2})\s+(\d{1,2}):(\d{2}))|((\w{3})\s+(\d{1,2})\s+' \
                                  '(\d{4})))\s+(?P<name>.+)$'
            match_obj = re.match(dir_listing_pattern, item)
            if match_obj:
                match_group_dict = match_obj.groupdict()
            is_dir = (match_group_dict['dir'] == 'd')
            item_name = match_group_dict['name']

            if is_dir:
                self.append_directory_tree(directory[1:], item_name, False)
                self.scan('{}/{}'.format(directory, item_name))
            else:
                self.connection.sendcmd("TYPE i")
                extension = item_name[-4:]
                if extension in ['.avi', '.mkv', '.mp4']:
                    if 'sample' not in item_name and 'Sample' not in item_name:
                        parent_directory = directory.split('/')[-1]
                        video_name = item_name.replace(extension, '')
                        video_info = self.video_info_finder.get_video_info(video_name, parent_directory)
                        video_info['filename'] = item_name
                        video_info['ip'] = self.ip_address
                        file_size = self.connection.size(directory+'/'+item_name)
                        video_info['filesize'] = self.sizeof_fmt(file_size)
                        video_info['parent_dir'] = parent_directory
                        try:
                            video_info['full_path'] = self.ip_address + directory + '/' + item_name.encode( 'ascii', 'replace' )
                        except Exception as the_e:
                            print self.ip_address
                            print directory
                            print item_name
                            #raise( the_e )
                        wx.CallAfter(self.main_app.process_new_result, result_dict=video_info)
                self.append_directory_tree(directory, item_name, True)
