# coding: utf-8

from abc import abstractmethod
from configdata import AbstConfigData
#from MyPackage.Metadata import ColumnNamer
import pprint
import pandas as pd
import datetime
import configparser
import sys
import os
import errno


#TODO: このファイル内にPublicメソッドは無いのでは？Privateメソッドの冒頭にアンダースコアを付けてPublicとPrivateを区別


#--------------------------------------------------------------------
# %%
class Interactor_FileConfig(AbstConfigData):
    def __init__(self, param_type_def_file_path, param_type_section_name, config_file_path):
        '''Constructor for Interactor_FileConfig, a config file parser.  
        Args:
            param_type_def_file_path (str): a path string indicating the file describing paramType definitions, the file having a section beginning with param_type_section_name, followed by a list of paramTypes and lists of  parameters each following a paramType they belong to following "="
                e.g., int_params = ['figure.dpi', 'font.size', 'axes.labelsize', 'lines.markersize', 'window.short', 'window.mid', 'window.long', 'n_clusters']
            param_type_section_name (str): a string indicating the section name that must be included in the paramType definition file
            config_file_path (str): a path string indicating the config file, which could be the same as the file indicated by param_type_def_file_path
        Returns:
            none
        '''
        self.config_file_path = config_file_path #configファイルとパラメタの型定義のファイルparam_type_def_file_pathが別であることも許容するため別引数にしている。
        super().__init__(param_type_def_file_path, param_type_section_name)
    #--------------------------------------------------------------------
    def setAllCfgDict(self):
        # Merely for backward compatibility
        # This function will not be called
        self.read_config()
    #--------------------------------------------------------------------
    # %%
    #@classmethod
    def read_config(self)->dict:
        """Sets up and returns a dictionary whose keys are section names and whose items are 
           dictionaries that relate parameter names to parameter values. Implementation required by abstConfigData
        Raises:
            FileNotFoundError: config file not found
            KeyError: parameter type not given in config file
        Returns:
            dictionary : a dictionary whose keys are section names and whose items are 
                        dictionaries that relate parameter names to parameter values, the parameter names
                        indicating the parameters that belong to the section identified by said section names.
                        
        """
        dict = {}
        if not os.path.exists(self.config_file_path):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self.config_file_path)
        rconfig = configparser.ConfigParser()
        rconfig.read(self.config_file_path, encoding='utf-8')

        for section in rconfig.sections():
        # ConfigParserであるrconfigの、paramType以外のセクションに、パラメタの値が文字列で
        # 読み込まれているので、先ほどの型変換規則に従い型変換する。
            if section != self.param_type_section_name:
                self.dict_all_config[section]={}
                #print(rconfig.items(section))
                d = {k:v for (k,v) in rconfig.items(section)}
                #d = dict(rconfig.items(section))　#なぜかdict()が dict object is not callableとされ型変換できない
                for paramName, paramValString in d.items():
#                for key, value in dict(rconfig.items(section)).items():
                    try: 
                        self.dict_all_config[section][paramName] = self.decode_value_string_to_value[paramName](paramValString) 
                    except KeyError:
                        assert 0, f"Parameter type for {paramName} not given in config file -> paramType section."
            else:
                pass
        return self.dict_all_config
    #--------------------------------------------------------------------
    def saveAllCfgDictWR(self, save_file_path: str):
        # merely for backward compatibility 
        self.save_all_config_dict(self, save_file_path)
    #--------------------------------------------------------------------
    # %%
    def save_all_config_dict(self, save_file_path: str):
        """書き出し用の共通設定辞書self.dict_all_configWR（key:セクション名、item:辞書）を設定ファイルに書き出す。

        Args:
            save_file_path (str): 書き出し用の共通設定辞書self.dict_all_configWRを書き出す先の設定ファイルの「パス＋ファイル名」
        """
        wconfig = configparser.ConfigParser()
        for section in self.dict_all_configWR.keys():
            wconfig[section] = self.dict_all_configWR[section]
            '''
            print("section={}".format(section))
            pprint.pprint(self.dict_all_configWR[section])
            wconfig[section] = {}
            for key, value in self.dict_all_configWR[section].items():
                print(key)
                wconfig[section][key] = value'''

        try:
            with open(save_file_path, 'w') as f_out:
                wconfig.write(f_out)
        except IOError as e:
            sys.exit('Cannot write to "{}": {}'.format(save_file_path, e))


