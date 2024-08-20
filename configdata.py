# coding: utf-8

from abc import  abstractmethod
#from ast import Str
#import MyPackage.Metadata as md
#from MyPackage.Metadata import ColumnNamer
import pprint
import pandas as pd
import datetime
import configparser
import sys
import os
import errno

# %%

#DONE: Publicメソッドは、'_config_section_to_dict’と'old_write_temp'だけでは？それ以外はメソッドの冒頭にアンダースコアを付けてPublicとPrivateを区別
#DONE: '_config_section_to_dict’と'old_write_temp'のメソッド名が分かりづら過ぎるからもっと簡潔な名称に直す
#DONE: ファイル内での記載順序に思想が無さすぎ読みづらい。記載順序を直す。

class AbstConfigData():
    # %%
    def __init__(self, param_type_def_file_path, param_type_section_name):
        """Sets up "dict_param_type", the parameter type dictionary indicating the mapping from parameter names to parameter types

        Args:
            param_type_def_file_path (str): A string indicating the path to "parameter definition file", the file defining the mapping from parameter names to parameter types
            param_type_section_name (str): A string indicating the name of "parameter type section" within the "parameter definition file", the section defining the mapping from parameter names to parameter types
        
        Raises:
            FileNotFoundError: If file designated by "param_type_def_file_path" is not found.
        """
        self.param_type_section_name = param_type_section_name
        if not os.path.exists(param_type_def_file_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), param_type_def_file_path)
        self.dict_param_type = {}
        self._set_dict_param_type(self.dict_param_type, param_type_def_file_path, param_type_section_name)
        self.dict_all_config = {}  #dictionary holding all the config values
        self.dict_all_configWR = {} #パラメタを外部に書き出す際に用いる共通の設定辞書。keyはセクション名、itemは、パラメタ名とパラメタ値をセットにする辞書。
        #self.dict_all_config = self.read_config()
        self.dict_functions = {} #たぶん不要？ dict_functions = {型名: 変換関数}
        self.dict_functions = self._set_func_dict()
        self.decode_value_string_to_value = {} #関数の辞書。decode_value_string_to_value = {パラメタ名: strからの変換関数}
        self._set_decode_functions()
        #self.dict_all_config = self.read_config()  #read_config()(旧setAllCfgDict())を外部とのインタフェースにする。

        #self.setParamsFromCfgParser(self.rconfig, 'paramType')
  
    #--------------------------------------------------------------------
    # %%
    #def _config_section_to_dict(self, outerDict: dict, specificCfgSection: str):
    def _config_section_to_dict(self, specificCfgSection: str):
        """設定辞書dict_all_configから所定のパラメタを読み出してouterDict(rcParams等を想定)に設定する。
        Args:
            outerDict (dict): Cfgファイルから読み込んだ設定値を書き込むディクショナリ（e.g., matplotlib.pyplot.rcParams）のデータの受け入れ先として明示的に渡す。
            specificCfgSection(str): outerDictに受け渡すべき、self.universalDict中のセクション
        Returns:
            outerDict
        """
        #TODO: そもそもが「_config_section_to_dict」とうたいながら、dict_all_configの中身をouterDictに書き出しているだけなのがおかしい。名が体を表すように直すべき。
        #当初はおそらく、ファイルから読み出すことによるConfigとWebからの設定によるConfigを並立する関係にしたかったのだろう。
        #しかし今の考えは、Webからの設定のためのInteractionはControllerコンポに入れておき、そちらからInteractorにある本クラスを叩くことにより設定を実現するというもの。
        #結局Webからの設定も、ファイルの読み書きに帰結するということ。だから上記並立関係はもはや不要という理解。
        #いや、思想は正しいのでは？DBから読み出して設定することもある。だから設定データは抽象化しておき、Interactorは切り分ける。
        #とすると間違っているのは、当初の思想を忘れて「setAllCfgDict2OuterDict()」を「_config_section_to_dict（）」にRenameした俺か。。
        
        outerDict = {}  # メソッドの引数からouterDictを外したことに伴う変更。以前は引数に渡さなければエラーになっていた気がするが、これで良いのだろうか。
        
        #TODO: 'SpecificCfgSection'を指定しない場合、すべてのセクションを書き出すようにしたい。
        #self.dict_all_config = self.read_config()
        if specificCfgSection not in self.dict_all_config.keys():
            raise KeyError("No {} section the config dictionary!!!".format(specificCfgSection))
        else:
            for key in self.dict_all_config[specificCfgSection]: 
                try: 
                    outerDict[key] = self.dict_all_config[specificCfgSection][key]
                except KeyError:
                    assert 0, "Unknown key in rcParams, plParams, or other outer dictionary does not have the corresponding value."
        return outerDict
    #--------------------------------------------------------------------
    # %%
    def old_write_temp(self, sectionName: str, outerDict: dict):
        """outerDict(rcParams等を想定)に設定されたパラメタの値を、共通の設定辞書self.dict_all_configWR（key:セクション名、item:辞書）の所定のセクションに設定し、
           最終的にファイルを書き出すことに備える。

        Args:
            sectionName (str): 書き出し用設定辞書dict_all_configWRのセクション名。このセクション名が後述のouterDictを格納するセクションを示す。
            outerDict (dict): 設定値を書き込んであるディクショナリ（e.g., matplotlib.pyplot.rcParams）。この中身をself.dict_all_configWRに複写する。
            specificCfgSection(str): outerDictの中身を格納すべき、self.dict_all_configWR中のセクションの名称。
        """
        self.dict_all_configWR[sectionName] = {}
        for key, value in outerDict.items():
            self.dict_all_configWR[sectionName][key] = str(value)
            #print("{}: {}, {}".format(key, value, str(value)))
    #--------------------------------------------------------------------
    # %%
    def _set_dict_param_type(self, dict_param_type, param_type_def_file_path, param_type_section_name):
        '''「パラメタの型の定義ファイル」からパラメタ名とその型の組を読み出し、paramTyepDictとしてパラメタと型変換関数の辞書を作成。
        前提として、param_type_def_file_pathにあるパラメタの型の定義ファイルのセクションparam_type_section_nameに、
        {'型1': ['par1', 'par2',..., 'par3'], '型2': ['par4', 'par5',..., 'par6']}の形式で
        型名とパラメタリストが格納されている。
        
        Args:
            dict_param_type (dict str: str): パラメタの名前と型の組を格納する辞書。AbstConfigDataのインスタンス変数。わざわざI/F経由で渡さなくても良いかも。
            param_type_def_file_path (str): パラメタの型の定義ファイルのパス。当ファイルのセクションparam_type_section_nameに、
                {'型1': ['par1', 'par2',..., 'par3'], '型2': ['par4', 'par5',..., 'par6']}の形式で
                型名とパラメタリストが記載されている。
            param_type_section_name (str): configファイル中で変数の型毎に変数名を羅列したセクションの名称。
            
        Returns:
            None    
        '''
        rconfig = configparser.ConfigParser()
        rconfig.read(param_type_def_file_path, encoding='utf-8')

        for paramType in dict(rconfig.items(param_type_section_name)):
        # 設定ファイルのセクションparamTypeに型毎にパラメタ一覧があるので、これを読むことにより、各パラメタの型を得る。
        # 例：
        # 　int_params = ['figure.dpi', 'font.size', 'axes.labelsize', 'lines.markersize']
        # 　bool_params = ['figure.autolayout', 'axes.grid', 'per_capita', 'set_date_range', 'add_line']
            paramsInParamType_str = _s2sList(rconfig[param_type_section_name].get(paramType)) 
            for param in paramsInParamType_str:
            # dict_functionsに、型毎に文字列からの型変換規則があるので、
            # 先ほど読み込んだパラメタに、各型に合わせて型変換規則を割り当てる。
                dict_param_type[param] = paramType  # e.g., dict_param_type['figure.dpi] = 'int_params'
    #--------------------------------------------------------------------
    # %%
    #@abstractclassmethod
    def read_config(self, *args) -> dict:
        """Builds a dictionary of config data from either a file or web page.
        This fuction only works as an interface and is implemented in the subclass 
        and is called from setParams().
        
        Returns:
            Dict string: any
        """
        assert 0, 'AbstConfigData.read_config() must be defined in the subclass!'
    #--------------------------------------------------------------------
    # %%
    def _set_decode_functions(self):
        """ Stores functions in the list 'self.decode_value_string_to_value[]', wherein the functions cast strings 
            into the parameter types given by the key of the list.
        """
        for param in self.dict_param_type:
            self.decode_value_string_to_value[param] = self.dict_functions[self.dict_param_type[param]]  # e.g., decode_value_string_to_value['figure.dpi'] = intFunc
    #--------------------------------------------------------------------
    # %%
    def _set_func_dict(self):
        """Sets up and returns a dictionary of functions that cast input strings to appropriate parameter types pursuant to given dictionary keys.
        Returns:
            dictionary : a dictionary of functions that cast an input string to appropriate parameter types pursuant to given dictionary keys
        """
        boolFunc = (lambda str: bool(True) if str=='True' else bool(False))
        intFunc = (lambda str: int(str))
        fFunc = (lambda str: float(str))
        sFunc = (lambda str: str)
        #fListFunc = (lambda str: [float(x.strip().strip("'")) for x in str.strip('\[\]\'').split(',')])
        fListFunc = (lambda str: _s2fList(str))
        #sListFunc = (lambda str: [x.strip().strip("'") for x in str.strip('\[\]').split(',')])
        sListFunc = (lambda str: _s2sList(str))
        siDictFunc = (lambda str: _s2siDict(str))
        ssDictFunc = (lambda str: _s2ssDict(str))
        dict_functions = { #　{型名: 関数}
            "bool_params"           : boolFunc,  # bool
            "int_params"            : intFunc,  # int. # No definition for int list?
            "float_params"          : fFunc,  # float
            "string_params"         : sFunc,  # string
            "float_list_params"     : fListFunc,  # float list
            "string_list_params"    : sListFunc, # string list
            "str_int_dict_params"   : siDictFunc,  # dictionary of string to int
            "str_str_dict_params"   : ssDictFunc  # dictionary of string to string
            }
        return dict_functions
        #print (dict_functions)
    #--------------------------------------------------------------------
    # %% Maintaining backwards compatibility
    #--------------------------------------------------------------------
    def setCfgParams2OuterDict(self, outerDict: dict, specificCfgSection: str):
        # merely for backward compatibility 
        self.dict_all_config = self.read_config()
        return self._config_section_to_dict(self, specificCfgSection)
    #--------------------------------------------------------------------
    def setOuterDict2AllCfgDictWR(self, sectionName: str, outerDict: dict):
        # merely for backward compatibility 
        self.old_write_temp(sectionName, outerDict)
    #--------------------------------------------------------------------
    def setAllCfgDict(self, *args):
        # merely for backward compatibility 
        self.read_config(self, *args)        
#--------------------------------------------------------------------
#--------------------------------------------------------------------
# %% Small functions
# https://note.nkmk.me/python-str-remove-strip/
def _s2fList(str):
    '''Converts string to a list of floats. The string should be written in the format as used in python code, i.e., '[0.0, 1.1, 2.2, 3.3]'
    Args:
        str (string): string to be converted into list of floats
    Returns:
        list of floats
    '''
    #print (str.strip())
    #大カッコを外しカンマでSplitしただけだと、stringのリストができ、その各stringは余計な空白やらが付着しており、かつアポストロフィを両サイドに伴っている。
    l_sf = [x.strip().strip("'") for x in (str.strip(r'\[\]')).split(',')]
    return [float(s) for s in l_sf]
#--------------------------------------------------------------------
def _s2sList(str):
    '''Converts string to a list of strings. The input string should be written in the format as used in python code, i.e., '['man', 'crane', 'turtle']'
    Args:
        str (string): string to be converted into list of strings
    Returns:
        list of strings
    '''
    l_st = [x.strip().strip("'") for x in (str.strip(r'\[\]')).split(',')]
    return l_st
#--------------------------------------------------------------------
def _s2siDict(str):
    '''Converts string to a dictionary of "string: integer". The string should be written in the format as used in python code, i.e., '{'man': 2, 'crane': 2, 'turtle': 4}'
    Args:
        str (string): string to be converted into dictionary of "string: integer"
    Returns:
        dictionary of "string: integer"
    '''
    d_sti = {}
    pairList = [x.strip() for x in (str.strip(r'\{\}')).split(',')]
    for item in pairList:
        pair = item.split(':')
        d_sti[pair[0].strip().strip("'")] = int(pair[1].strip())
    return d_sti
#--------------------------------------------------------------------
def _s2ssDict(str):
    '''Converts string to a dictionary of "string: string". The string should be written in the format as used in python code, i.e., '{'man': 'mammal', 'crane': 'bird', 'turtle': 'reptile'}'
    Args:
        str (string): string to be converted into dictionary of "string: string"
    Returns:
        dictionary of "string: string"
    '''
    d_ss = {}
    pairList = [x.strip() for x in (str.strip(r'\{\}')).split(',')]
    for item in pairList:
        pair = item.split(':')
        d_ss[pair[0].strip().strip("'")] = pair[1].strip().strip("'")
    return d_ss
#--------------------------------------------------------------------
#TODO: finish up this function for designating multiple config files illustrating different attributes for different air compressor products
# 違うか。_s2ssDictで良い気がしてきた。
# ’confgFigFileName'という辞書に{'prod01': 'file01.xlsx', 'prod02': 'file02.xslx', 'prod03.xlsx': 'file03.xlsx'}、
# 'formulaSheetName'という辞書に{'prod01': 'formula', 'prod02': 'formula', 'prod03': 'formula1}というようになれば良い。 
def _s2sdictDict(str):
    '''Converts string to a dictionary of "string: dict(string: string)". 
    The string should be written in the format as used in python code, i.e.,
    'John': ['male', '48', {'man': 'mammal', 'crane': 'bird', 'turtle': 'reptile'}'
    Args:
        str (string): string to be converted into dictionary of "string: string"
    Returns:
        dictionary of "string: string"
    '''
#--------------------------------------------------------------------
def pri(num, item):
    print("[{}] item: {}; ({})".format(num, item, type(item)))
#--------------------------------------------------------------------



         