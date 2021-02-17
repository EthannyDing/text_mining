# -*- coding: utf-8 -*-

# utils: file input and output
#
# Author: Renxian Zhang, Owen Lu 
# --------------------------------------------------
# This module implements functions to faciliate common file IO tasks.
# Including: Excel, Word, CSV, XML

import csv, re, os, shutil, time
import xlrd, xlsxwriter


class OS:    
    """Wrappers for OS-level operations
    """
    
    def __init__(self):
        """Intialize an OS instance.        
        """
        
        pass
    
    def makeDirectory(self, directoryPath):
        """Make a directory if it does not exist; 
           otherwise delete the existing one and create a new one
           
           Args:
              directoryPath (str): the path of the directory
        """
        
        retry = True
        if os.path.exists(directoryPath):
            shutil.rmtree(directoryPath)
        while retry:
            try:               
                time.sleep(0.001)
                os.makedirs(directoryPath)
            except OSError as e:                
                if e.errno != 13: # eaccess
                    raise
            else:
                retry = False   
                
    def copyFile(self, srcPath, dstPath):
        """A wrapper of shutil.copy2 that deals with exceptions
           
           Args:
              srcPath (str): the path to move from
              dstPath (str): the path to move to
        """
        
        retry = True
        
        while retry:
            try:               
                time.sleep(0.001)
                shutil.copy2(srcPath, dstPath)
            except:                
                pass
            else:
                retry = False    
    
    def moveFile(self, srcPath, dstPath):
        """A wrapper of shutil.move that deals with exceptions
           
           Args:
              srcPath (str): the path to move from
              dstPath (str): the path to move to
        """
        
        retry = True
        
        while retry:
            try:               
                time.sleep(0.001)
                shutil.move(srcPath, dstPath)
            except:                
                pass
            else:
                retry = False   
                
    def renameFile(self, srcPath, dstPath):
        """A wrapper of os.rename that deals with exceptions
           
           Args:
              srcPath (str): the source path with the old name
              dstPath (str): the target path with the new name
        """
        
        retry = True
        
        while retry:
            try:               
                time.sleep(0.001)
                if os.path.exists(dstPath):
                    os.remove(dstPath)
                os.renames(srcPath, dstPath)
            except:                
                pass
            else:
                retry = False        
       

class TXTReader:
    """Read a txt file
    """
    
    def __init__(self, inputPath, encoding='utf8'):
        """Intialize a TXTReader instance.
        
           Args:        
              inputPath (str): The path of the txt file
              encoding (str): the encoding method
        """        
        
        self._reader = open(inputPath, 'rb')
        self._encoding = encoding

    def readToString(self):
        """Read the raw text content of the txt file.
                                             
           Returns: 
              (str): raw text content as a string
        """            
        
        res = self._reader.read().decode(self._encoding)
        
        self._reader.close()

        return res    

    def read(self, stripText=False):
        """Read the text content of the txt file.
                           
           Args:
              stripText (bool): whether to strip the text
                                
           Returns: 
              (list): a list of strings from the lines
        """            
        
        if stripText:
            res = [line.decode(self._encoding).strip() for line in self._reader]
        else:
            res = [line.decode(self._encoding) for line in self._reader]
        
        self._reader.close()

        return res


class TXTWriter:
    """Write a txt file
    """
    
    def __init__(self, outputPath, encoding='utf8', mode='wb'):
        """Intialize a TXTWriter instance.
        
           Args:        
              outputPath (str): The path of the txt file
              encoding (str): the encoding method
              mode (str): the write mode
        """        
        
        self._writer = open(outputPath, mode)
        self._encoding = encoding

    def writeFromString(self, text):
        """Write text content as a string to a txt file.
        
           Args:
              text (str): text to be written
        """            
        
        self._writer.write(text.encode(self._encoding))
        self._writer.close()    

    def write(self, texts):
        """Write text content to a txt file.
        
           Args:
              texts (list): text contents to be written
        """            
        
        self._writer.writelines([(line + '\n').encode(self._encoding) for line in texts])
        self._writer.close()


class CSVReader:    
    """Read a csv file
    """    
    
    def __init__(self, inputPath, encoding='utf8', cleanEOL=True, delimiter=','):        
        """Initialize a CSVReader instance.
        
           Args:
               inputPath (str): The path of the csv file
               encoding (str): the encoding method
               cleanEOL (bool): Whether the EOL in the source file needs to be cleaned first
                                If True, a new cleaned file will be created and saved   
               delimiter (str): the delimiter used in the csv file                       
        """
        
        csv.field_size_limit(100000000)
        
        if cleanEOL == True:
            raw = open(inputPath, 'r', newline='', errors='ignore').read()
            cleaned = re.sub(r'\r', '', raw)
            rootPath, filename = os.path.split(inputPath)
            base, ext = os.path.splitext(filename)
            cleanedPath = os.path.join(rootPath, base + '_cleaned' + ext)
            open(cleanedPath, 'w', encoding=encoding).write(cleaned)
            self._csv = csv.reader(open(cleanedPath, 'r', newline='', encoding=encoding), delimiter=delimiter)
        else:
            self._csv = csv.reader(open(inputPath, 'r', newline='', encoding=encoding), delimiter=delimiter)
                
    def read(self, hasHeader=True):        
        """Read the text content of the csv file.
           
           Args:
               hasHeader (bool): Whether the csv file has a header
           
           Returns: 
               (tuple): (header (str), body (list) of text contents)
        """        
        
        content = list(self._csv)
        
        if hasHeader:
            header, body = content[0], content[1:]
        else:
            header, body = [], content
            
        return header, body
    
    
class CSVWriter:
    """Write a csv file.
    """
    
    def __init__(self, outputPath, encoding='utf8'):
        """Initialize a CSVWriter instance.
        
           Args:
              outputPath (str): The path of the csv file        
              encoding (str): the encoding method
        """
        
        self.f = open(outputPath, 'w', newline='', encoding=encoding)
        self._csv = csv.writer(self.f)
        
    def write(self, header, body):
        """Write the csv file with header and body.
           
           Args:
               header (str): The header of the csv file
                             If '' or None, the csv file will have no header
               body (list): text contents to be written           
        """ 
        
        if header:
            self._csv.writerow(header)
        self._csv.writerows(body)  
        self.f.close()       
        

class ExcelReader:
    """Read an Excel file
    """
    
    def __init__(self, inputPath, worksheetIndex=None, worksheetName=None):
        """Initialize a ExcelReader instance.
        
           Args:
               inputPath (str): The path of the Excel file        
               worksheetIndex (int): The index of the worksheet
               worksheetName (str): The name of the worksheet
        """    
                
        self.workbook = xlrd.open_workbook(inputPath)
        self.worksheets = self.workbook.sheet_names()
        
        if not (worksheetIndex or worksheetName):
            self.worksheet = self.workbook.sheet_by_index(0)
        elif worksheetIndex:
            self.worksheet = self.workbook.sheet_by_index(worksheetIndex)
        else:
            self.worksheet = self.workbook.sheet_by_name(worksheetName)

    def _convertToString(self, cells):
        """Convert raw cell values (numbers) to strings.
        
           Args:
               cells (list): A list of cell values to be converted
               
           Returns:
               (list): Converted cell values in strings
        """
                
        res = list(map(lambda x: x.ctype==2 and str(int(x.value)) or str(x.value), cells))
        
        return res

    def readCell(self, row, col):
        """Read a cell, the value type of which is automatically decided.
           It should not be used if the numbers are to be interpreted as strings.
           In that case, use readCellAsString instead
        
           Args:
               row (int): The row index of the cell
               col (int): The column index of the cell
               
           Returns:
               The cell value, the type of which is automatically decided.
        """        
                
        res = self.worksheet.cell_value(row, col)
        
        return res
    
    def readCellRaw(self, row, col):
        """Read a cell in its raw format.
        
           Args:
               row (int): The row index of the cell
               col (int): The column index of the cell
               
           Returns:
               The cell's raw value
        """ 
        
        res = self.worksheet.cell(row, col)
        
        return res
    
    def readCellAsString(self, row, col):
        """Read a cell as a string.
        
           Args:
               row (int): The row index of the cell
               col (int): The column index of the cell
               
           Returns:
               (str): The cell's value as a string
        """
        
        cells = [self.readCellRaw(row, col)]
        
        return self._convertToString(cells)[0]
        
    def readRow(self, row, startCol, endCol=None):
        """Read a row, the value type of which is automatically decided.
           It should not be used if the numbers are to be interpreted as strings.
           In that case, use readRowAsString instead
        
           Args:
               row (int): The row index
               startCol (int): The index of the start column
               endCol (int): The index of the end column; if None, read till the end
               
           Returns:
               (list): A list of cell values in the row, the types of which are automatically decided.
        """ 
        
        if endCol:
            res = self.worksheet.row_values(row, startCol, endCol+1)
        else:
            res = self.worksheet.row_values(row, startCol)
        
        return res
    
    def readRowRaw(self, row, startCol, endCol=None):
        """Read a row in its raw format.
                   
           Args:
               row (int): The row index
               startCol (int): The index of the start column
               endCol (int): The index of the end column; if None, read till the end
               
           Returns:
               (list): A list of cell values in their raw formats.
        """        
        
        if endCol:
            res = self.worksheet.row(row)[startCol:endCol+1]
        else:
            res = self.worksheet.row(row)[startCol:]
            
        return res
            
    def readRowAsString(self, row, startCol, endCol=None):
        """Read a row as a list of strings
        
           Args:
               row (int): The row index
               startCol (int): The index of the start column
               endCol (int): The index of the end column; if None, read till the end
               
           Returns:
               (list): A list of cell values as strings.
        """ 
        
        cells = self.readRowRaw(row, startCol, endCol)
        
        return self._convertToString(cells)    
    
    def readCol(self, col, startRow, endRow=None):
        """Read a column, the value type of which is automatically decided.
           It should not be used if the numbers are to be interpreted as strings.
           In that case, use readColAsString instead
        
           Args:
               col (int): The column index
               startRow (int): The index of the start row
               endRow (int): The index of the end row; if None, read till the end
               
           Returns:
               (list): A list of cell values in the column, the types of which are automatically decided.
        """ 
        
        if endRow:
            res = self.worksheet.col_values(col, startRow, endRow+1)
        else:
            res = self.worksheet.col_values(col, startRow)
        
        return res
    
    def readColRaw(self, col, startRow, endRow=None):
        """Read a column in its raw format.
                   
           Args:
               col (int): The column index
               startRow (int): The index of the start row
               endRow (int): The index of the end row; if None, read till the end
               
           Returns:
               (list): A list of cell values in their raw formats.
        """ 
        
        if endRow:
            res = self.worksheet.col(col)[startRow:endRow+1]
        else:
            res = self.worksheet.col(col)[startRow:]
            
        return res
            
    def readColAsString(self, col, startRow, endRow=None):
        """Read a column as a list of strings
        
           Args:
               col (int): The column index
               startRow (int): The index of the start row
               endRow (int): The index of the end row; if None, read till the end
               
           Returns:
               (list): A list of cell values as strings.
        """
        
        cells = self.readColRaw(col, startRow, endRow)
        
        return self._convertToString(cells)
    
    def readAllRows(self):
        """Read all cells in the Excel worksheet in rows, the value type of which is automatically decided.
           It should not be used if the numbers are to be interpreted as strings.
           In that case, use readAllRowsAsString instead

           Returns: 
               (list): a list of lists (rows) of all items in a sheet, with the value types automatically decided
        """
        
        res = []
                
        numRows = self.worksheet.nrows
        for idx in range(numRows):
            res.append(self.readRow(idx, 0))
        
        return res    
    
    def readAllRowsAsString(self):
        """Read all cells in the Excel worksheet in rows as strings

           Returns: 
               (list): a list of lists (rows) of all items in a sheet as strings
        """
        
        res = []
                
        numRows = self.worksheet.nrows
        for idx in range(numRows):
            res.append(self.readRowAsString(idx, 0))
        
        return res   
    
    def readAllCols(self):
        """Read all cells in the Excel worksheet in columns, the value type of which is automatically decided.
           It should not be used if the numbers are to be interpreted as strings.
           In that case, use readAllColsAsString instead

           Returns: 
               (list): a list of lists (columns) of all items in a sheet, with the value types automatically decided
        """
        
        res = []
                
        numCols = self.worksheet.ncols
        for idx in range(numCols):
            res.append(self.readCol(idx, 0))
        
        return res    
    
    def readAllColsAsString(self):
        """Read all cells in the Excel worksheet in columns as strings

           Returns: 
               (list): a list of lists (columns) of all items in a sheet as strings
        """
        
        res = []
                
        numCols = self.worksheet.ncols
        for idx in range(numCols):
            res.append(self.readColAsString(idx, 0))
        
        return res    
    
class ExcelWriter:
    """Write an Excel file
    """
    
    def __init__(self, outputPath, stringsToUrls=False):
        """Initialize a ExcelWriter instance.
        
           Args:
               outputPath (str): The path of the Excel file        
               stringsToUrls (bool): Whether url strings are to be converted to the url format
        """        
        
        self.workbook = xlsxwriter.Workbook(outputPath, {'strings_to_urls': stringsToUrls})
        self.worksheets = {}
           
    def addWorksheet(self, worksheetName=None):
        """Add a worksheet by name.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
                                    If None, the default name like Sheet1 will be used
        """        
        
        if not worksheetName:
            worksheet = self.workbook.add_worksheet()
        else:
            worksheet = self.workbook.add_worksheet(name=worksheetName) 
        self.worksheets[worksheet.name] = worksheet

    def commit(self):
        """Commit the write
        """
        
        self.workbook.close()

    def formatRow(self, worksheetName, row, height=None, cellFormat=None):
        """Format a row.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
               row (int): The index of the row
               height (int): The height of the row
                             If None, the default is used
               cellFormat (str or dict): The cell formatting information
                                         Two supported str values are 'text_wrap' and 'bold'
        """
        
        if type(cellFormat) == str:
            if cellFormat == 'text_wrap':
                cf = self.workbook.add_format()
                cf.set_text_wrap()
            elif cellFormat == 'bold':
                cf = self.workbook.add_format()
                cf.set_bold()            
            else:
                cf = None
        elif type(cellFormat) == dict:      
            cf = self.workbook.add_format(cellFormat)        

        self.worksheets[worksheetName].set_row(row, height, cell_format=cf)    
            
    def formatCol(self, worksheetName, startCol, endCol, width=None, cellFormat=None):
        """Format a column.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
               startCol (int): The index of the start column
               endCol (int): The index of the end column
               width (int): The width of the column
                            If None, the default is used
               cellFormat (str or dict): The cell formatting information
                                         Two supported str values are 'text_wrap' and 'bold'
        """
        
        if type(cellFormat) == str:
            if cellFormat == 'text_wrap':
                cf = self.workbook.add_format()
                cf.set_text_wrap()
            elif cellFormat == 'bold':
                cf = self.workbook.add_format()
                cf.set_bold()        
            else:
                cf = None
        elif type(cellFormat) == dict:      
            cf = self.workbook.add_format(cellFormat)
        else:
            cf = None
        
        self.worksheets[worksheetName].set_column(startCol, endCol, width, cell_format=cf)
            
    def writeCell(self, worksheetName, row, col, value, *args):
        """Write a cell.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
               row (int): The row index of the cell
               col (int): The column index of the cell
               value: The cell value to be written
        """
        
        self.worksheets[worksheetName].write(row, col, value, *args)
     
    def writeRow(self, worksheetName, row, startCol, values, *args):
        """Write a row.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
               row (int): The index of the row
               startCol (int): The index of the start column
               values (list): A list of cell values to be written
        """
        
        self.worksheets[worksheetName].write_row(row, startCol, values, *args)
    
    def writeCol(self, worksheetName, startRow, col, values, *args):
        """Write a column.
        
           Args:
               worksheetName (str): The name of the worksheet to be added
               startRow (int): The index of the start row
               col (int): The index of the column
               values (list): A list of cell values to be written
        """
        
        self.worksheets[worksheetName].write_column(startRow, col, values, *args)


