import wxversion
wxversion.select( "3.0" )
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class SuperListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):

    ITEM_ID_OFFSET = 100

    def __init__(self, parent, columns, style=None):
        default_style = wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES
        if style is not None:
            style = default_style | style
        else:
            style = default_style
        super(SuperListCtrl, self).__init__(parent=parent, style=style)
        ListCtrlAutoWidthMixin.__init__(self)
    
        for col, heading in enumerate(columns):
            self.InsertColumn(heading=heading, col=col)
    
        self.custom_data = { }

    def get_item_custom_data( self, item_idx ):
        """
        Get the custom data associated with an item based on its index.
        @param item_idx: The index of the item data has been requested for.
        @type item_idx: int
        @return: If the index is valid return the custom data, otherwise
        return None.
        """
        # get item's custom ID
        ID = self.GetItemData( item_idx )
        if ID != 0:
            return self.custom_data.get( ID, None )
        else:
            return None

    def set_item_custom_data( self, item_idx, data ):
        """
        Set custom data for the given item index.
        @param item_idx: The index of the item to set custom data for.
        @type item_idx: int
        @param data: The data to be associated with the item at the given
        index
        @return: None
        """
        # ItemData holds unique ID of this item.
        
        if self.GetItemData( item_idx ) == 0:
            # if ItemData has not yet been set,
            # assign the original index plus an offset to be its ID
            self.SetItemData( item_idx, item_idx + self.ITEM_ID_OFFSET )
        
        # get item's custom ID
        ID = self.GetItemData( item_idx )
        
        # update custom_data for this item
        self.custom_data.update( { ID: data } )

    def add_row(self, row_data):
        num_rows = self.GetItemCount()
        row_index = None
        # Convert any unicode strings to ascii
        row_data = [str(data).encode('ascii', 'ignore') for data in row_data]
        for idx, column_value in enumerate(row_data):
            if row_index is None:
                row_index = self.InsertStringItem(index=num_rows, label=row_data[idx])
                self.SetColumnWidth(idx, wx.LIST_AUTOSIZE)
            else:
                self.SetStringItem(row_index, idx, column_value)

        return row_index

    def get_column_rows(self, column_index):
        column_data = []

        item = self.GetNextItem(-1)
        while item != -1:
            column_data.append(self.GetItemText(item=item, col=column_index))

        return column_data

    def get_column_names(self):
        column_names = []

        num_columns = self.GetColumnCount()
        for column_number in range(num_columns):
            column_names.append(self.GetColumn(column_number).GetText())

        return column_names

    def get_all_rows(self):
        rows = []
        column_names = self.get_column_names()

        item = self.GetNextItem(-1)
        while item != -1:
            current_row = {}
            for column_num, column_name in enumerate(column_names):
                current_row[column_name] = self.GetItemText(item, col=column_num)
            rows.append(current_row.copy())
            item = self.GetNextItem(item)

        return rows