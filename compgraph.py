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
packageFilePath = os.getcwd() + getSlash() + '..' + getSlash() + '..' + getSlash() + 'MyPackage'
#test_packageFilePath = os.getcwd() + getSlash() + 'readCalc6' 
sys.path.append(packageFilePath)
##sys.path.append(test_packageFilePath)
print(packageFilePath)

import re
from abc import abstractmethod
import pandas as pd
import numpy as np
import itertools
import datautil as du
import fileconfig as fc
#import debugutils as dbu

debugFlag = True

#sys.path.append(packageFilePath)
#print(sys.path)

def graph_to_lisp(graph_file_path:str, graph_sheet_name:str=None, graph_header=None, graph_usecols=None, graph_index_col=None, config_file_path=None, debugMode:bool=False):
    cgr = CompGraphReader(graph_file_path=graph_file_path, graph_sheet_name=graph_sheet_name, graph_header=graph_header, graph_usecols=graph_usecols, graph_index_col=graph_index_col, 
                          config_file_path=config_file_path, debugMode=debugMode)
    return cgr.graph_to_formula()

def graph_to_dict_of_lisp_definitions(graph_file_path:str, graph_sheet_name:str=None, graph_header=None, graph_usecols=None, graph_index_col=None, config_file_path=None, debugMode:bool=False):
    cgr = CompGraphReader(graph_file_path=graph_file_path, graph_sheet_name=graph_sheet_name, graph_header=graph_header, graph_usecols=graph_usecols, graph_index_col=graph_index_col, 
                          config_file_path=config_file_path, debugMode=debugMode)
    return cgr.graph_to_formula(format='dict')
#------------------------------------------------------------------------------ 
#------------------------------------------------------------------------------ 
class AbstCompGraphReader():
#    def __init__(self, file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None, debugMode:bool=False):
    def __init__(self, debugMode:bool=False):
        self.debugMode = debugMode
        self.formulas = {}
        
        self.number_of_open_formulas = 0
        self.southern_limit_so_far = 0
        
        #self.graph_to_formula()
    #----------------------------------------------------------------
    @abstractmethod
    def graph_to_formula(self, *args, **kwargs)->str:
        assert 0, "graph_to_formula() must be implemented in the subclass"
    #----------------------------------------------------------------
    @abstractmethod
    def update(self, *args, **kwargs)->str:
        assert 0, "update() must be implemented in the subclass"
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
            # スペース相当。excelを読み込むときにスペースを'--'で埋めたため。
            if self._is_connector(value):
                self._show_value(f'found connector', row, col)
                return self._process_connector(value, row, col)

            elif self._is_operator(value):
                self._show_value(f'found operator', row, col)
                return self._process_operator(value, row, col)                         

            else:
                self._show_value(f'found non-number and non-operator string', row, col)
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
    @abstractmethod
    def _is_operator(self, *args, **kwargs)->str:
        assert 0, "_is_operator() must be implemented in the subclass"
    #----------------------------------------------------------------
    @abstractmethod
    def _process_operator(self, *args, **kwargs)->str:
        assert 0, "_process_operator() must be implemented in the subclass"
    #----------------------------------------------------------------
    @abstractmethod
    def _is_connector(self, *args, **kwargs)->str:
        assert 0, "_is_connector() must be implemented in the subclass"
    #----------------------------------------------------------------
    @abstractmethod
    def _process_connector(self, *args, **kwargs)->str:
        assert 0, "_process_connector() must be implemented in the subclass"
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
class CompGraphReader(AbstCompGraphReader):
#    def __init__(self, file_path:str, sheet_name:str=None, header=None, usecols=None, index_col=None, 
    def __init__(self, graph_file_path:str=None,  graph_sheet_name:str=None, graph_header=None, graph_usecols=None, graph_index_col=None, 
                 config_file_path='config_comp_graph.ini', param_type_section_name='param_type', 
                 debugMode:bool=False):

        # CompGraphReaderのインスタンス自体の設定。演算子の辞書、コネクタの辞書を設定する
        _param_type_def_file_path = self.config_file_path = config_file_path
        _cfg = fc.Interactor_FileConfig(_param_type_def_file_path, param_type_section_name=param_type_section_name, config_file_path=config_file_path)
        _comp_graph_params = _cfg.read_config()['comp_graph_params']
        self.dict_operators     = _comp_graph_params['operators']
        self.dict_connectors    = _comp_graph_params['connectors']
        self.dict_actions = {"check_right": self._check_right_of, 
                             "check_down": self._check_down_from, 
                             "glance_down": self._glanceDownFrom}
        
        # 計算グラフの設定。(i)グラフのファイルとワークシートの指定、(ii)グラフから参照されるデータ（変数や配列）のファイルとワークシートの指定、(iii)そのワークシートの読み込み時の設定など。
        _io_params = _cfg.read_config()['IO_params']
        self.graph_file_path    = _io_params['graph_file_path'] if graph_file_path is None else graph_file_path
        self.graph_sheet_name         = _io_params['graph_sheet_name'] if graph_sheet_name is None else graph_sheet_name
        self.graph_header       = _io_params.get('graph_header') if graph_header is None else graph_header
        self.graph_usecols      = _io_params.get('graph_usecols') if graph_usecols is None else graph_usecols
        self.graph_index_col    = _io_params.get('graph_index_col') if graph_index_col is None else graph_index_col
        self.start_mark         = _io_params.get('start_mark')
        
        super().__init__(debugMode=debugMode)
    #----------------------------------------------------------------
    #@classmethod
    def graph_to_formula(self, format=None):
        # 呼び出し側でメインで使うメソッド。エクセルから計算グラフを読み出し、LISP表現にして返す。
        #self.showValue(f'create equation for',row, col)
        self.graph_df = pd.read_excel(self.graph_file_path, sheet_name=self.graph_sheet_name, 
                                      header=self.graph_header, usecols=self.graph_usecols, index_col=self.graph_index_col).fillna('--')
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
    def update(self, graph_file_path=None, graph_sheet_name=None, graph_header=None, graph_usecols=None, graph_index_col=None, debugMode=None, format=None)->str:
        if graph_file_path is not None:     self.gaph_file_path     = graph_file_path
        if graph_sheet_name is not None:    self.graph_sheet_name   = graph_sheet_name
        if graph_header is not None:        self.graph_header       = graph_header
        if graph_usecols is not None:       self.graph_usecols      = graph_usecols
        if graph_index_col is not None:     self.graph_index_col    = graph_index_col
        if debugMode is not None:           self.debugMode          = debugMode
        
        self.number_of_open_formulas = 0
        self.southern_limit_so_far = 0
        
        return self.graph_to_formula(format)
    #----------------------------------------------------------------
    def _is_operator(self, value):
        if value in itertools.chain.from_iterable(self.dict_operators['valid'].values()):  # see study/dictionary/iterable.ipynb
            return True
        elif value in itertools.chain.from_iterable(self.dict_operators['invalid'].values()):
            assert 0, f"Invalid operator found: {value} .\n Exiting...(1)"
        else:
            return False
    #----------------------------------------------------------------
    def _process_operator(self, value, row, col):
        # 演算子相当であるかをチェック。__init__()で演算子の辞書dict_operatorsを作ってある。
        # 前提：dict_operatorsは、dict["valid"/"invalid"][演算子]=[左記演算子の記載のバリエーションのリスト]という形式
        for k,v in self.dict_operators['valid'].items():
            if value in v: 
                value = k  # 表記ゆれを統合する。
                return f'( {value} {self._check_down_from(row,col)} {self._check_right_of(row, col)} )'
        
        # 事前に_is_operator()でスクリーニングしているから、基本的にこのループには来ず削っても良いはずだが念のため。
        for k,v in self.dict_operators['invalid'].items():
            if value in v: 
                value = k
                assert 0, f'Invalid operator found: "{value}".\n Exiting...(2)\n'
    #----------------------------------------------------------------
    def _is_connector(self, value):
        pattern_list = []
        for k,v in self.dict_connectors.items():
            pattern_list += v['patterns']
        if value in pattern_list:
            return True
        else:
            return False
    #----------------------------------------------------------------
    def _process_connector(self, value, row, col) -> str:
        # コネクタ相当であるかチェック。__init__()で演算子の辞書dict_connectorsを作ってある。
        # 前提：dict_connectorsは、dict[コネクタ][pattern/action]=(patternの場合)[左記コネクタの記載のバリエーションのリスト]、(actionの場合)右か下かを指定する文字列という形式
        for k,v in self.dict_connectors.items():
            if value in v['patterns']:
                value = k  # 表記ゆれを統合する。
                return self.dict_actions[self.dict_connectors[value]['action']](row, col)
#--------------------------------------------------------------------
#--------------------------------------------------------------------

if __name__ == '__main__' :
    import pprint
    #import Interactor_FileConfig20231128 as ifc
    import fileconfig as fc
    #params = {}
    #cfg_path = r'..\MyDev\data\config.ini'
    cfg_path = r'config_comp_graph.ini'
    cgr = CompGraphReader(cfg_path, debugMode=False)
    #cfg = fc.Interactor_FileConfig(cfg_path, 'paramType', cfg_path)
    #params = cfg.read_config('IOParams')
    #io_params = (cfg.read_config())['IOParams']
    #io_params = cfg._config_section_to_dict('IOParams')
    #df = CompGraphReader.read_formula_file(params['graph_file_path'], sheet_name=params['graph_sheet_name'])
    #cgr = CompGraphReader(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    #lisp = graph_to_lisp(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    lisp = cgr.graph_to_formula()
    print(f'formulas in lisp:\n{lisp}\n')
    #pprint.pprint(cgr.formulas_in_dict())
    #dict_lisp = graph_to_dict_of_lisp_definitions(io_params['graph_file_path'], sheet_name=io_params['graph_sheet_name'], debugMode=False)
    #dict_lisp = cgr.graph_to_formula(format='dict')
    #print(f'formulas in dict:\n')
    #pprint.pprint(dict_lisp)
    #print(dict_lisp)
  
    #cgr.update(sheet_name='Sheet8')
    #print(f'formulas in dict:')
    #pprint.pprint(cgr.formulas_in_dict())
    #print(f'formulas in lisp: {cgr.formulas_in_lisp()}')

    
    
    
# %%
