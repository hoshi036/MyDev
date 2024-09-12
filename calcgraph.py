import platform
def getSlash():
    pf = platform.system()
    # pri(1, pf)
    if pf=='Windows': slash='\\'
    elif pf=='Linux': slash='/'
    elif pf=='Darwin': slash='/'
    else: assert 0, 'Unknown platform!!'
    
    return slash

import os
import sys

packageFilePath = os.getcwd() + getSlash() + '..' + getSlash() + 'MyPackage'
#test_packageFilePath = os.getcwd() + getSlash() + 'readCalc6' 
sys.path.append(packageFilePath)
##sys.path.append(test_packageFilePath)
print(packageFilePath)

import re
from abc import abstractmethod
import pandas as pd
import numpy as np
import datautil as du
#import debugutils as dbu

debugFlag = True

#sys.path.append(packageFilePath)
#print(sys.path)

def graph_to_lisp(file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None, debugMode:bool=False):
    cgr = CalcGraphReader(file_path, sheet_name, header, usecols, index_col, debugMode)
    return cgr.graph_to_formula()

def graph_to_dict_of_lisp_definitions(file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None, debugMode:bool=False):
    cgr = CalcGraphReader(file_path, sheet_name, header, usecols, index_col, debugMode)
    return cgr.graph_to_formula(format='dict')
#------------------------------------------------------------------------------ 
#------------------------------------------------------------------------------ 
class CalcGraphReader():
    def __init__(self, file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None, debugMode:bool=False):
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.header = header
        self.usecols = usecols
        self.index_col = index_col
        self.debugMode = debugMode
        self.formulas = {}
        
        self.number_of_open_formulas = 0
        self.southern_limit_so_far = 0
        
        #self.graph_to_formula()
    #----------------------------------------------------------------
    def update(self, file_path=None, sheet_name=None, header=None, usecols=None, index_col=None, debugMode=None, format=None)->str:
        if file_path is not None: self.file_path = file_path
        if sheet_name is not None: self.sheet_name = sheet_name
        if header is not None: self.header = header
        if usecols is not None: self.usecols = usecols
        if index_col is not None: self.index_col = index_col
        if debugMode is not None: self.debugMode = debugMode
        
        self.number_of_open_formulas = 0
        self.southern_limit_so_far = 0
        
        return self.graph_to_formula(format)
    #----------------------------------------------------------------
    #@classmethod
    def graph_to_formula(self, format=None):
        #self.showValue(f'create equation for',row, col)
        self.graph_df = pd.read_excel(self.file_path, sheet_name=self.sheet_name, header=self.header, usecols=self.usecols, index_col=self.index_col).fillna('--')
        #self.formulas = list()

        self.pos = [0,0]
        while(self.southern_limit_so_far+1 < self.graph_df.shape[0]):
            self._read_cell(int(self.pos[0]), int(self.pos[1]))
            self.pos[0] = max(self.southern_limit_so_far+1, self.pos[0]+1)
            self.pos[1] = 0
        if format in [None, 'lisp']:
            return self.formulas_in_lisp()
        elif format == 'dict':
            return self.formulas_in_dict()
        else:
            print('unknown format desgnatd: returning "lisp"')
            return self.formulas_in_lisp()
    #----------------------------------------------------------------
    def formulas_in_lisp(self):
        lisp_expression = ""
        for value in self.formulas.values():
            lisp_expression += value
        return lisp_expression
    #----------------------------------------------------------------
    def formulas_in_dict(self):
        return self.formulas
    #----------------------------------------------------------------
    def _read_cell(self, row, col)->str:
        value = self._check_value(row,col)
        if du.is_num(value):  # str.isnumeric()だと、マイナスの付く数字や小数は、Falseに判定されてしまうため、is_num()を独自に定義。
            self._show_value('found number', row, col)
            self.southern_limit_so_far = max(self.southern_limit_so_far, row)
            return value
        else:
            value = value.strip()
            if value == '--':
                self._show_value('found "None"', row, col)
                return self._check_right_of(row, col)
            #elif du.is_num(value):  # str.isnumeric()だと、マイナスの付く数字や小数は、Falseに判定されてしまうため、is_num()を独自に定義。
            #    self._show_value('found number', row, col)
            #    self.southern_limit_so_far = max(self.southern_limit_so_far, row)
            #    return value
            #elif value.isalpha():
            elif value in ['+', '＋']:
                self._show_value('found"+"', row, col)
                return f"( + {self._check_down_from(row,col)} {self._check_right_of(row, col)} )"
            elif value in ['*', '＊', '×']:
                self._show_value('found "*"', row, col)
                return f"( * {self._check_down_from(row,col)} {self._check_right_of(row, col)} )"
            elif value in ['@', '＠']:
                self._show_value('found "@"', row, col)
                return f"( @ {self._check_down_from(row,col)} {self._check_right_of(row, col)})"
            elif value in ['**', '＊＊']:
                self._show_value('found "**"', row, col)
                return f"( ** {self._check_down_from(row,col)} {self._check_right_of(row, col)})"
            elif value in ['│', '|']:
                self._show_value('found "│"', row, col)
                return self._check_down_from(row,col)
            elif value in ['└', '`']:
                self._show_value('found "└"', row, col)
                return self._check_right_of(row, col)
            elif value == ('-' or 'ー'):
                self._show_value('found "-"', row, col)
                assert 0, 'unallowed character "-" found"\n'
            elif value in ['/', '／']:
                self._show_value('found "/"', row, col)
                assert 0, 'unallowed character "/" found"\n'
            else:
                self._show_value('found non-number and non-operator string', row, col)
                if self._glanceDownFrom(row, col) in ["=","＝"]:
                    self._show_value('found "=". Beginning new formula', row, col)
                    self.number_of_open_formulas += 1
                    dict_entry_formula = self._create_formula(row, col)
                    self.number_of_open_formulas -= 1
                    self._add_formula(dict_entry_formula)
                    return value
                    #return self.check(row+1, col+1)
                else:
                    self._show_value('end', row, col)
                    self.southern_limit_so_far = max(self.southern_limit_so_far, row)
                    return value
            #else:
            #    assert 0, 'Unexpected value found\n'
    #----------------------------------------------------------------
    #@classmethod
    #def read_formula_file(cls, file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None)->pd.DataFrame:
    #    #self.showValue(f'create equation for',row, col)
    #    return pd.read_excel(file_path, sheet_name=sheet_name, header=header, usecols=usecols, index_col=index_col).fillna('--')
    #----------------------------------------------------------------      
    def _check_value(self, row, col):
        self._show_value('_check_value', row, col)
        return self.graph_df.iloc[ row, col ]
    #----------------------------------------------------------------
    def _show_value(self, buf, row, col):
        # debugModeのときに値を示す
        print(f"{buf}:[{row},{col}]={self.graph_df.iloc[row,col]}") if self.debugMode else None
    #----------------------------------------------------------------
    def _create_formula(self, row, col):
        self._show_value(f'create formula for',row, col)
        return dict({self.graph_df.iloc[row, col]: f"(define {self.graph_df.iloc[row, col]} {self._read_cell(row+1, col+1)})"})
    #----------------------------------------------------------------
    def _add_formula(self, dict_entry_formula):
        if(self.debugMode): print(f'(1) adding formula "{dict_entry_formula.values()}" to "{self.formulas_in_lisp()}"')
        #self.formulas.append(formula)
        self.formulas |= dict_entry_formula
    #----------------------------------------------------------------
    def _glanceDownFrom(self, row, col)->str:
        if row+1 == self.graph_df.shape[0]:
            self._show_value('glanceDownAndCrossesBoundary', row, col)
            return '\0'
        else:
            self._show_value('_glanceDownFrom', row, col)
            return self._check_value(row+1, col)
    #----------------------------------------------------------------
    def _check_right_of(self, row, col)->str:
        if col+1 == self.graph_df.shape[1]: #check right boundary
            if self.number_of_open_formulas > 0:
                assert 0, '_check_right_of: out of right boundary\n'
            else:
                return
        else:
            return self._read_cell(row, col+1)
    #----------------------------------------------------------------
    def _check_down_from(self, row, col)->str:
        self.southern_limit_so_far = max(self.southern_limit_so_far, row)
        if row+1 == self.graph_df.shape[0]: #check bottom boundary
            assert 0, '_check_down_from: out of bottom boundary\n'
        else:
            return self._read_cell(row+1, col)
#--------------------------------------------------------------------
#--------------------------------------------------------------------

if __name__ == '__main__' :
    import pprint
    #import Interactor_FileConfig20231128 as ifc
    import fileconfig as fc
    #params = {}
    cfg_path = r'..\MyDev\data\config.ini'
    cfg = fc.Interactor_FileConfig(cfg_path, 'paramType', cfg_path)
    #params = cfg.read_config('IOParams')
    io_params = (cfg.read_config())['IOParams']
    #io_params = cfg._config_section_to_dict('IOParams')
    #df = CalcGraphReader.read_formula_file(params['graph_file_path'], sheet_name=params['graph_sheet_name'])
    #cgr = CalcGraphReader(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    lisp = graph_to_lisp(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    print(f'formulas in lisp:\n{lisp}')
    #pprint.pprint(cgr.formulas_in_dict())
    dict_lisp = graph_to_dict_of_lisp_definitions(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    print(f'formulas in dict:\n')
    pprint.pprint(dict_lisp)
    #print(dict_lisp)
  
    #cgr.update(sheet_name='Sheet8')
    #print(f'formulas in dict:')
    #pprint.pprint(cgr.formulas_in_dict())
    #print(f'formulas in lisp: {cgr.formulas_in_lisp()}')

    
    
    
# %%
