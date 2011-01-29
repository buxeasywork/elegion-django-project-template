import datetime
import xlwt
from xlwt import *

from django.db.models.query import QuerySet, ValuesQuerySet
from django.http import HttpResponse


def choose_format_cell(value):
    styles = {'datetime': xlwt.easyxf(num_format_str='yyyy-mm-dd hh:mm:ss'),
      'date': xlwt.easyxf(num_format_str='yyyy-mm-dd'),
      'time': xlwt.easyxf(num_format_str='hh:mm:ss'),
      'default': xlwt.Style.default_style}
    if isinstance(value, datetime.datetime):
        cell_style = styles['datetime']
    elif isinstance(value, datetime.date):
        cell_style = styles['date']
    elif isinstance(value, datetime.time):
        cell_style = styles['time']
    else:
        cell_style = styles['default']
    return cell_style


class ExcelCell:
    # borderX - means borderX size, columns - means, how many column merge,
    # alignment means alignment. can be left, right, top, bottom, center
    def __init__(self, value, border_top=0, border_bottom=0, border_left=0, border_right=0, columns = 1,
                    horiz_alignment = 'center', vertical_alignment = 'center', font_height = 10,
                    col_width = 0x0d00, row_height = 0x0100, wrap = False):
        self.value = value
        self.style = None
        self.columns = columns
        self.style = XFStyle()
        border = Borders()
        border.left = border_left
        border.right = border_right
        border.top = border_top
        border.bottom = border_bottom
        self.style.borders = border
        self.style.num_formats = choose_format_cell(value)
        alignment = Alignment()
        font = Font()
        font.height = font_height * 20
        self.style.font = font
        if horiz_alignment == 'left':
            alignment.horz = Alignment.HORZ_LEFT
        elif horiz_alignment == 'right':
            alignment.horz = Alignment.HORZ_RIGHT
        else:
            alignment.horz = Alignment.HORZ_CENTER
        if vertical_alignment == 'top':
            alignment.vert = Alignment.VERT_TOP
        elif vertical_alignment == 'bottom':
            alignment.vert = Alignment.VERT_BOTTOM
        else:
            alignment.vert = Alignment.VERT_CENTER
        if wrap:
            alignment.wrap = Alignment.WRAP_AT_RIGHT
        self.style.alignment = alignment
        self.col_width = col_width
        self.row_height = row_height


class ExcelResponse(HttpResponse):
    def __init__(self, data, output_name='excel_data', headers=None,
                 force_csv=False, encoding='utf8'):

        # Make sure we've got the right type of data to work with
        valid_data = False
        if isinstance(data, ValuesQuerySet):
            data = list(data)
        elif isinstance(data, QuerySet):
            data = list(data.values())
        if hasattr(data, '__getitem__'):
            if isinstance(data[0], dict):
                if headers is None:
                    headers = data[0].keys()
                data = [[row[col] for col in headers] for row in data]
                data.insert(0, headers)
            if hasattr(data[0], '__getitem__'):
                valid_data = True
        assert valid_data is True, "ExcelResponse requires a sequence of sequences"

        import StringIO
        output = StringIO.StringIO()
        # Excel has a limit on number of rows; if we have more than that, make a csv
        use_xls = False
        if len(data) <= 65536 and force_csv is not True:
            use_xls = True
        if use_xls:
            book = xlwt.Workbook(encoding=encoding)
            sheet = book.add_sheet('Sheet 1')
            sheet.header_str = ""
            sheet.footer_str = ""
            for rowx, row in enumerate(data):
                colx_merged = 0
                height = 0x0100
                #exit(sheet.row(rowx).height)
                for colx, value in enumerate(row):
                    if isinstance(value, ExcelCell):
                        sheet.write_merge(rowx, rowx, colx_merged, colx_merged + value.columns - 1, value.value, value.style)
                        colx_merged = colx_merged + value.columns
                        sheet.col(colx_merged-1).width = value.col_width
                        if height < value.row_height:
                            height = value.row_height
                    else:
                        cell_style = choose_format_cell(value)
                        sheet.write(rowx, colx_merged, value, style=cell_style)
                        colx_merged = colx_merged + 1
                        sheet.col(colx_merged).width = 0x0700
                sheet.row(rowx).height = height
                sheet.row(rowx).height_mismatch = 1
            book.save(output)
            mimetype = 'application/vnd.ms-excel'
            file_ext = 'xls'
        else:
            # Add Byte Order Mark (BOM) to make Excel understand UTF-8 encoding
            output.write('\xEF\xBB\xBF')
            for row in data:
                out_row = []
                for value in row:
                    if not isinstance(value, basestring):
                        value = unicode(value)
                    value = value.encode(encoding)
                    out_row.append(value.replace('"', '""'))
                output.write('"%s"\n' %
                             '","'.join(out_row))
            mimetype = 'text/csv'
            file_ext = 'csv'
        output.seek(0)
        super(ExcelResponse, self).__init__(content=output.getvalue(),
                                            mimetype=mimetype)
        self['Content-Disposition'] = 'attachment;filename="%s.%s"' % \
            (output_name.replace('"', '\"'), file_ext)

