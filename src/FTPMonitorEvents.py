import wxversion
wxversion.select( "3.0" )
import wx


EVT_RESULT_FOUND_ID = wx.NewId()
def BindResultFoundEvent( gui_window, callback ):
    """Define Result Found Event."""
    gui_window.Connect( -1, -1, EVT_RESULT_FOUND_ID, callback )

class ResultFoundEvent( wx.PyEvent ):
    """Event to post when a search result has been found"""

    def __init__( self, search_result_data ):
        """Initialize event"""
        wx.PyEvent.__init__( self )
        self.SetEventType( EVT_RESULT_FOUND_ID )
        self.data = search_result_data
