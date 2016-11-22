import wxversion
wxversion.select( "3.0" )
import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class SuperListCtrl(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, columns):
        super(SuperListCtrl, self).__init__(parent=parent, style=wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES)
        ListCtrlAutoWidthMixin.__init__(self)

        for col, heading in enumerate(columns):
            self.InsertColumn(heading=heading, col=col)

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