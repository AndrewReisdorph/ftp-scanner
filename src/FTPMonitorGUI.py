# Built ins
import threading
import os

# wxpython
import wxversion
wxversion.select("3.0")
import wx

# Project modules
import FTPCrawler
from AddFTPSourceDialog import AddFTPSourceDialog
from SuperListCtrl import SuperListCtrl
import ftp_service_comm
import ftp_download_service

ADD_SOURCE_TOOL_ID = wx.NewId()
SCAN_SOURCES_TOOL_ID = wx.NewId()
DOWNLOAD_TOOL_ID = wx.NewId()
STOP_SCAN_TOOL_ID = wx.NewId()
CANCEL_DL_ID = wx.NewId()
REMOVE_DL_ID = wx.NewId()

release_groups = ['klaxxon']

class UnableToConnect( Exception ):
    pass


class AddDownloaderDialog( wx.Dialog ):
    """
    This module creates a dialog for exporting data from selected search results.
    """
    
    def __init__( self, parent ):
        """
        Initialize GUI
        @param parent: The results list control that launches this dialog.
        @type parent: SortedListCtrl
        @param main_app: A reference to the main Scorpion GUI
        @type main_app: ScorpionGUI
        @return: None
        """
        wx.Dialog.__init__( self, parent, title="Add Downloader", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER )
        self.parent = parent
        #self.Bind( wx.EVT_CLOSE, self.on_close )
        
        self.init_gui( )

    def init_gui( self ):
        main_vsizer = wx.BoxSizer( wx.VERTICAL )
        options_gridsizer = wx.GridBagSizer( hgap=5, vgap=5 )

        ip_label = wx.StaticText( parent=self, label="IP:" )
        #self.ip_text_ctrl = wx.TextCtrl( parent=self, value="127.0.0.1" )
        self.ip_text_ctrl = wx.TextCtrl( parent=self, value="meltzserver.mooo.com" )

        port_label = wx.StaticText( parent=self, label="Port:" )
        #self.port_text_ctrl = wx.TextCtrl( parent=self, value=str( ftp_service_comm.DEFAULT_PORT ) )
        self.port_text_ctrl = wx.TextCtrl( parent=self, value=str( 8844 ) )

        add_button = wx.Button( parent=self, label="Ok" )
        add_button.Bind( wx.EVT_BUTTON, self.add_callback )

        options_gridsizer.Add( item=ip_label, pos=( 0, 0 ) )
        options_gridsizer.Add( item=self.ip_text_ctrl, pos=( 0, 1 ) )
        options_gridsizer.Add( item=port_label, pos=( 1, 0 ) )
        options_gridsizer.Add( item=self.port_text_ctrl, pos=( 1, 1 ) )

        main_vsizer.Add( options_gridsizer, flag=wx.ALL, border=5 )
        main_vsizer.Add( add_button, flag=wx.GROW | wx.LEFT | wx.RIGHT, border = 5 )

        self.SetSizer( main_vsizer )
        main_vsizer.Fit( self )
        self.Layout( )

    def add_callback( self, event ):
        ip = self.ip_text_ctrl.GetValue( )
        port = int( self.port_text_ctrl.GetValue( ) )
        self.parent.add_downloader( ip, port )
        self.EndModal( 0 )


class FTPMonitorGUI(wx.Frame):

    def __init__(self):
        frame_style = wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX | wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX
        super(FTPMonitorGUI, self).__init__(None, style=frame_style)

        self.sources_listctrl = None
        self.scan_button = None
        self.results_listctrl = None
        self.progress_bar = None
        self.log_textctrl = None
        self.quit_request = False

        self.init_ui()

        self.Bind( wx.EVT_CLOSE, self.on_quit_cleanup )

        self.destinations = [ ]
        self.active_downloader = None

        #self.sources_listctrl.add_row(['67.172.255.177', '/Public/Movies'])
        self.add_downloader( 'local' )
        #self.sources_listctrl.add_row(['24.162.163.232', '/shares/STAR/movies'])

    def init_ui(self):
        self.Title = 'FTP Monitor'
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        icon_bundle = wx.IconBundle()
        icon_bundle.AddIconFromFile(r'../resources/cheeseburger.ico', wx.BITMAP_TYPE_ANY)
        self.SetIcons(icon_bundle)

        # Setup Toolbar
        toolbar = self.CreateToolBar()
        add_source_image = wx.Image(r'../resources/add_32.png').ConvertToBitmap()
        scan_source_image = wx.Image(r'../resources/scan_32.png').ConvertToBitmap()
        download_image = wx.Image(r'../resources/download_32.png').ConvertToBitmap()
        stop_image = wx.Image(r'../resources/stop.png').ConvertToBitmap()
        toolbar.AddTool(ADD_SOURCE_TOOL_ID, bitmap=add_source_image)
        toolbar.AddTool(SCAN_SOURCES_TOOL_ID, bitmap=scan_source_image)
        toolbar.AddTool(DOWNLOAD_TOOL_ID, bitmap=download_image)
        toolbar.AddTool(STOP_SCAN_TOOL_ID, bitmap=stop_image)
        toolbar.Realize()
        self.Bind(event=wx.EVT_TOOL, id=ADD_SOURCE_TOOL_ID, handler=self.add_source_button_callback)
        self.Bind(event=wx.EVT_TOOL, id=SCAN_SOURCES_TOOL_ID, handler=self.scan_sources_button_callback)
        self.Bind(event=wx.EVT_TOOL, id=DOWNLOAD_TOOL_ID, handler=self.download_button_callback)
        self.Bind(event=wx.EVT_TOOL, id=STOP_SCAN_TOOL_ID, handler=self.stop_scan_button_callback)

        splitter = wx.SplitterWindow(parent=self)

        sources_panel = wx.Panel(parent=splitter)
        sources_label = wx.StaticText(parent=sources_panel, label='Sources')
        self.sources_listctrl = SuperListCtrl(parent=sources_panel, columns=['IP', 'Search Path'])

        downloaders_label_hsizer = wx.BoxSizer( wx.HORIZONTAL )
        downloaders_label = wx.StaticText(parent=sources_panel, label='Downloaders')
        add_downloader_button = wx.Button( parent=sources_panel, label='+' )
        add_downloader_button.Bind( wx.EVT_BUTTON, self.add_downloader_callback )
        downloaders_label_hsizer.Add( item=downloaders_label, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=5 )
        downloaders_label_hsizer.Add( item=add_downloader_button, flag=wx.TOP | wx.BOTTOM, border=5 )
        self.downloaders_listctrl = SuperListCtrl(parent=sources_panel, columns=['IP'], style=wx.LC_SINGLE_SEL)
        self.downloaders_listctrl.Bind( wx.EVT_LIST_ITEM_SELECTED, self.downloaders_on_select )

        sources_panel_vsizer = wx.BoxSizer(wx.VERTICAL)
        sources_panel_vsizer.Add(item=sources_label)
        sources_panel_vsizer.Add(item=self.sources_listctrl, flag=wx.EXPAND, proportion=1)
        sources_panel_vsizer.Add(item=downloaders_label_hsizer)
        sources_panel_vsizer.Add(item=self.downloaders_listctrl, flag=wx.EXPAND, proportion=1)
        sources_panel.SetSizer(sources_panel_vsizer)

        results_panel = wx.Panel(parent=splitter)
        results_label = wx.StaticText(parent=results_panel, label='Results')
        results_columns = ['Title', 'Series', 'Episode Number', 'Season', 'Rating', 'Genre', 'Duration',
                           'IMDB Rating', 'Resolution', 'Year', 'File Size', 'IP', 'Filename', 'Full Path']
        self.results_listctrl = SuperListCtrl(parent=results_panel, columns=results_columns)
        results_panel_vsizer = wx.BoxSizer(wx.VERTICAL)
        results_panel_vsizer.Add(results_label)
        results_panel_vsizer.Add(self.results_listctrl, flag=wx.EXPAND, proportion=1)
        results_panel.SetSizer(results_panel_vsizer)

        splitter.SplitVertically(sources_panel, results_panel)
        splitter.SetMinimumPaneSize(300)

        self.progress_bar = wx.Gauge(parent=self)


        splitter2 = wx.SplitterWindow(parent=self)
        log_panel = wx.Panel(parent=splitter2)
        log_label = wx.StaticText(parent=log_panel, label='Log')
        self.log_textctrl = wx.TextCtrl(parent=log_panel, style=wx.TE_READONLY | wx.TE_MULTILINE)
        log_panel_vsizer = wx.BoxSizer(wx.VERTICAL)
        log_panel_vsizer.Add( log_label )
        log_panel_vsizer.Add( self.log_textctrl, flag=wx.EXPAND, proportion=1 )
        log_panel.SetSizer( log_panel_vsizer )

        downloads_panel = wx.Panel(parent=splitter2)
        downloads_label = wx.StaticText(parent=downloads_panel, label='Downloads')
        self.downloads_listctrl = SuperListCtrl(parent=downloads_panel, columns=[ 'Status', 'Progress', 'Source', 'File', 'Rate' ])
        self.downloads_listctrl.Bind( event=wx.EVT_LIST_ITEM_RIGHT_CLICK, handler=self.download_right_click_callback )
        downloads_panel_vsizer = wx.BoxSizer(wx.VERTICAL)
        downloads_panel_vsizer.Add( downloads_label )
        downloads_panel_vsizer.Add( self.downloads_listctrl, flag=wx.EXPAND, proportion=1 )
        downloads_panel.SetSizer( downloads_panel_vsizer )

        # downloads right-click callback
        self.downloads_context_menu = wx.Menu( )
        self.downloads_context_menu.Append( CANCEL_DL_ID, 'Cancel' )
        self.downloads_context_menu.Append( REMOVE_DL_ID, 'Remove' )

        splitter2.SplitVertically( log_panel, downloads_panel )
        splitter2.SetMinimumPaneSize(300)

        main_vsizer = wx.BoxSizer(wx.VERTICAL)
        main_vsizer.Add(splitter, flag=wx.EXPAND | wx.ALL, proportion=4, border=5)
        main_vsizer.Add(self.progress_bar, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
        main_vsizer.Add(splitter2, flag=wx.EXPAND | wx.ALL, proportion=1, border=5)
        #main_vsizer.Add(self.log_textctrl, flag=wx.EXPAND | wx.ALL, proportion=1, border=5)

        self.SetSizer(main_vsizer)

        self.Show()
        self.SetSize((800, 500))

    def process_new_result(self, result_dict):
        row_data = []
        keys = ['title', 'series', 'episode', 'season', 'mpaa', 'genres', 'runtime', 'rating',
                'screen_size', 'year', 'filesize', 'ip', 'filename', 'full_path']

        for key in keys:
            value = result_dict.get(key, '-')
            if value is None:
                value = '-'
            row_data.append(value)

        #print '\tRAW:',result_dict
        #print '\tNEW ROW:',row_data

        self.log(result_dict)
        self.results_listctrl.add_row(row_data)

    def log(self, message):
        self.log_textctrl.AppendText(str(message)+'\n')

    def stop_scan_button_callback(self, event):
        event.Skip()
        self.quit_request = True

    def add_source_button_callback(self, event):
        event.Skip()

        add_source_dialog = AddFTPSourceDialog(self)
        add_source_dialog.ShowModal()

        if add_source_dialog.canceled:
            pass
        else:
            self.sources_listctrl.add_row([add_source_dialog.ip, add_source_dialog.path])

    def scanner_worker(self, sources):
        for source in sources:
            self.log('Scanning {} -> {}'.format(source['IP'], source['Search Path']))
            crawler = FTPCrawler.FTPCrawler(source['IP'], source['Search Path'], self)
            crawler.connect()
            crawler.scan()

    def scan_sources_button_callback(self, event):
        if event:
            event.Skip()
        sources = self.sources_listctrl.get_all_rows()
        scanning_thread = threading.Thread(target=self.scanner_worker, args=(sources,))
        scanning_thread.start()

    def download_button_callback(self, event):
        event.Skip()
        rows = self.results_listctrl.get_all_rows( )
        selected = -1
        if self.active_downloader is not None:
            # add files to downloader
            while True:
                selected = self.results_listctrl.GetNextSelected( selected )
                if selected == -1:
                    break
                row = rows[ selected ]
                new_filename = '{} ({})'.format( row[ 'Title' ], row[ 'Year' ] )
                new_filename = new_filename + os.path.splitext( row[ 'Filename' ] )[ 1 ]
                url = r'ftp://' + row[ 'Full Path' ]
                self.active_downloader.add_file_to_queue( url, new_filename )

            self.update_downloads_list( self.active_downloader )


    def add_downloader( self, ip, port=ftp_service_comm.DEFAULT_PORT ):
        if ip == 'local':
            downloader = ftp_download_service.DownloadService( )
            downloader.start( )
            downloader.host_ip = 'local'
        else:
            downloader = ftp_service_comm.Client( ip, host_port=port )

        try:
            # try to get downloader status
            stat = downloader.get_overall_status( )
            print stat
        except:
            raise( UnableToConnect( 'Could not connect to downloader' ) )

        self.destinations.append( downloader )
        row_index = self.downloaders_listctrl.add_row( [ downloader.host_ip ] )
        self.downloaders_listctrl.set_item_custom_data( row_index, downloader )
        self.update_downloads_list( downloader )

    def update_downloads_list( self, downloader ):
        # clear current list
        self.downloads_listctrl.DeleteAllItems( )
        try:
            # try to get downloader status
            overall_status = downloader.get_overall_status( )
        except:
            print 'Unable to connect to downloader'
            return

        for status in overall_status:
            row_data = [ status.get( name, '?' ) for name in self.downloads_listctrl.get_column_names( ) ]
            idx = self.downloads_listctrl.add_row( row_data )
            self.downloads_listctrl.set_item_custom_data( idx, status )

        self.active_downloader = downloader

    def downloaders_on_select( self, event ):
        selected_idx = self.downloaders_listctrl.GetFirstSelected( )
        if selected_idx > -1:
            downloader = self.downloaders_listctrl.get_item_custom_data( selected_idx )
            self.update_downloads_list( downloader )

    def add_downloader_callback( self, event ):
        dlg = AddDownloaderDialog( self )
        dlg.ShowModal( )
        dlg.Destroy( )

    def download_right_click_callback( self, event ):
        selected_idx = event.GetIndex()
        # bind callback to copy results option
        self.Bind( wx.EVT_MENU, lambda e: self.cancel_download( selected_idx ), id=CANCEL_DL_ID )
        self.Bind( wx.EVT_MENU, lambda e: self.remove_download( selected_idx ), id=REMOVE_DL_ID )

        # show context menu
        self.PopupMenu( self.downloads_context_menu, wx.GetMousePosition() )

    def cancel_download( self, selected_idx ):
        status = self.downloads_listctrl.get_item_custom_data( selected_idx )
        self.active_downloader.cancel_file_download( status['uid'] )
        self.update_downloads_list( self.active_downloader )

    def remove_download( self, selected_idx ):
        status = self.downloads_listctrl.get_item_custom_data( selected_idx )
        self.active_downloader.remove_file_download( status['uid'] )
        self.update_downloads_list( self.active_downloader )

    def on_quit_cleanup( self, event ):
        for dest in self.destinations:
            dest.stop( )

        event.Skip( )


def main():
    app = wx.App()
    FTPMonitorGUI()
    app.MainLoop()


if __name__ == '__main__':
    main()
