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
import compgraph as cg
#import debugutils as dbu

debugFlag = True

class DataReader():
    def __init__(self, data_file_path=None, param_type_def_file_path=None, param_type_section_name='param_type', config_file_path='config.ini'):
        self.config_file_path = config_file_path
        self.param_type_def_file_path = self.config_file_path if param_type_def_file_path is None else param_type_def_file_path
        
        cfg = fc.Interactor_FileConfig(self.param_type_def_file_path, param_type_section_name, self.config_file_path)
        params = cfg.read_config()['IO_params']
        self.data_file_path = params['data_file_path'] if data_file_path is None else data_file_path
        self.data_attributes = params.get('data_attributes')
    #----------------------------------------------------------------
    def read_data(self, df_dict):
        # エクセルから読み出した表をDFとして読み出し、データ名をキーに当辞書に登録する。
        # df_dictはdf_dict[データ名][製品識別子]というように、複合キーでDFを格納している。

        for key, attr_dict in self.data_attributes.items():  # ここでのkeyはデータフレームに対応するデータ名であって、設定ファイルで言う'general'や'timeSeriesData2'のようなもの。カラム名ではない。
            df_dict[key] = {}
            df = pd.read_excel(self.data_file_path, 
                            sheet_name=attr_dict['sheet_name'],
                            header    =attr_dict.get('header'),  # "multi_prod"＝＝”True”のとき、"header"は整数リスト。
                            usecols   =attr_dict.get('usecols'),  # "[]"でなくget()を使う理由は、.get()だとキーが存在しないときNoneが返るため。
                            index_col =attr_dict.get('index_col'))
            if attr_dict.get('multi_prod') != 'True':
                df_dict[key]['common'] = df
            else:  # 'multi_prod'=="True"のとき、次を必要とする：
                # - カラムがmulti_indexになっていること
                # - multi_indexのlevel0が製品識別子になっていること
                for product in df.columns.get_level_values(0).unique():
                    df_dict[key][product] = df.loc[:, product]  # productに対応するテーブル（DF）を辞書に登録

        return df_dict
    #----------------------------------------------------------------
    def set_data_for_product(self, prod_id, df_dict, item_dict_by_product, item_dict_common)->dict:
        # 製品識別子prod_idを指定して、データ項目辞書item_dict_by_productにデータを紐づける。
        # 前提として、df_dictは[データ名][製品識別子]という複合キーでDFを格納している。
        # テーブル（DF）毎の属性を格納するJSONデータdata_attributesから、次を読み出し使う：
        # - テーブルの向き'align'
        # - データのトリムの必要性'trim_by_max_year'とそのトリム幅'max_year'
        for key, attr_dict in self.data_attributes.items():
            if prod_id in df_dict[key]:
                df = df_dict[key][prod_id]
                match attr_dict['align']:
                    # 縦型のデータの場合
                    case 'vertical':
                        # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                        if attr_dict.get('trim_by_max_length')=='True':
                            #TODO: max_yearやmax_lengthというキーワードをハードコーディングしているのは最悪。
                            df = du.trim_DF(df, item_dict_common['max_length'])  # この時点でitem_dictにmax_yearが入っている必要あり
                        for col_name in df.columns:
                            item_dict_by_product.update({col_name: df[col_name]})
                    # 横型のデータの場合
                    case 'horizontal':
                        # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                        if attr_dict.get('trim_by_max_length')=='True':
                            df = du.trim_DF(df, item_dict_common['max_length'], axis=1)  # この時点でitem_dictにmax_yearが入っている必要あり
                        for row_name in df.index:
                            item_dict_by_product.update({row_name: df.loc[row_name, 'value']})
                    # マトリックス型データの場合
                    case 'matrix':
                        # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                        if attr_dict.get('trim_by_max_length')=='True':
                            df = du.trim_DF(df, item_dict_common['max_length'], axis=2)  # この時点でitem_dictにmax_yearが入っている必要あり
                        item_dict_by_product.update({key: np.array(df)})
                    case "_":
                        assert 0, ('Unknown data alignment designated2')
                        
        return item_dict_by_product
#--------------------------------------------------------------------
#--------------------------------------------------------------------

if __name__ == '__main__' :
    
    cfg_path = 'config_comp_graph.ini'
    
    data_reader = DataReader(config_file_path=cfg_path)
    df_dict = {}  
    df_dict = data_reader.read_data(df_dict=df_dict)

    #graph_file = params['IOParams']['graph_file_path']
    #graph_sheet = params['IOParams']['graph_sheet_name']
    #data_attributes = params['IOParams']['data_attributes']
    
    lisp = cg.graph_to_lisp('freeCashFlow_W_maxLength.xlsx', graph_sheet_name='formula3', config_file_path=cfg_path, debugMode=True)
    #lisp = cg.graph_to_lisp(graph_file, sheet_name=graph_sheet)
    #cfg.write_config('save.txt')
    print(lisp)

                    
    # まずはエクセルのワークシートからDFとしてデータを読み出し、df_dictに登録する。

    item_dict = {}  
    item_dict['common'] = {}
    item_dict['common'] = data_reader.set_data_for_product('common', df_dict, item_dict_by_product=item_dict['common'], item_dict_common=item_dict['common'])

    product_list = ['prod_01', 'prod_02']

    for product in product_list:
        item_dict[product] = {}
        item_dict[product] = data_reader.set_data_for_product(product, df_dict, item_dict_by_product=item_dict[product], item_dict_common=item_dict['common'])

    import pprint

    pprint.pprint(item_dict)

    import lispy as lp

    li = {}
    for prod in product_list:
        li[prod] = lp.LispInterpreter()
        li[prod].env |= item_dict['common']
        li[prod].env |= item_dict[prod]

        li[prod].interpret(f'(begin{lisp})')
        FCF = li[prod].interpret('FCF')

        import matplotlib.pyplot as plt

        plt.plot(range(45), FCF)
        plt.show()


    
    
    
# %%
