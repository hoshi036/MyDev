# %%
import sys
packageFilePath = r'..\..\MyPackage'
devFilePath = r'..\..\MyDev'
sys.path.append(packageFilePath)
sys.path.append(devFilePath)

import fileconfig as fc
import calcgraph as cg
import datautil as du

import pandas as pd
import numpy as np
from IPython.display import display


def read_data_file(data_file_path, data_attributes, df_dict):
    # エクセルから読み出した表をDFとして読み出し、データ名をキーに当辞書に登録する。
    # df_dictはdf_dict[データ名][製品識別子]というように、複合キーでDFを格納している。

    for key, attr_dict in data_attributes.items():  # ここでのkeyはデータフレームに対応するデータ名であって、設定ファイルで言う'general'や'timeSeriesData2'のようなもの。カラム名ではない。
        df_dict[key] = {}
        df = pd.read_excel(data_file_path, 
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

def set_data_for_product(prod_id, df_dict, data_attributes, item_dict_by_product, item_dict_common)->dict:
    # 製品識別子prod_idを指定して、データ項目辞書item_dict_by_productにデータを紐づける。
    # 前提として、df_dictは[データ名][製品識別子]という複合キーでDFを格納している。
    # テーブル（DF）毎の属性を格納するJSONデータdata_attributesから、次を読み出し使う：
    # - テーブルの向き'align'
    # - データのトリムの必要性'trim_by_max_year'とそのトリム幅'max_year'
    for key, attr_dict in data_attributes.items():
        if prod_id in df_dict[key]:
            df = df_dict[key][prod_id]
            match attr_dict['align']:
                # 縦型のデータの場合
                case 'vertical':
                    # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                    if attr_dict.get('trim_by_max_year')=='True':
                        df = du.trim_DF(df, item_dict_common['max_year'])  # この時点でitem_dictにmax_yearが入っている必要あり
                    for col_name in df.columns:
                        item_dict_by_product.update({col_name: df[col_name]})
                # 横型のデータの場合
                case 'horizontal':
                    # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                    if attr_dict.get('trim_by_max_year')=='True':
                        df = du.trim_DF(df, item_dict_common['max_year'], axis=1)  # この時点でitem_dictにmax_yearが入っている必要あり
                    for row_name in df.index:
                        item_dict_by_product.update({row_name: df.loc[row_name, 'value']})
                # マトリックス型データの場合
                case 'matrix':
                    # 最大年数によるデータトリムが指定されていたら、データをその範囲でトリムする
                    if attr_dict.get('trim_by_max_year')=='True':
                        df = du.trim_DF(df, item_dict_common['max_year'], axis=2)  # この時点でitem_dictにmax_yearが入っている必要あり
                    item_dict_by_product.update({key: np.array(df)})
                case "_":
                    assert 0, ('Unknown data alignment designated2')
                    
    return item_dict_by_product

# %%
#cfg_path = 'config.ini'
cfg_path = 'configFCF.ini'
cfg = fc.Interactor_FileConfig(cfg_path, 'paramType', cfg_path)
params = cfg.read_config()['IOParams']

lisp = cg.graph_to_lisp(params['graph_file_path'], 
                        sheet_name=params['graph_sheet_name'])

#cfg.write_config('save.txt')
#print(lisp)

df_dict = {}  
                
# まずはエクセルのワークシートからDFとしてデータを読み出し、df_dictに登録する。
#df_dict = read_data_file(params['IOParams']['data_file_path'], data_attributes=data_attributes, df_dict=df_dict)
df_dict = read_data_file(params['data_file_path'], 
                         data_attributes=params['data_attributes'], 
                         df_dict=df_dict)

item_dict = {}  

# 製品が１つの場合は、'prod_01', 'prod_02'などと指定せず'common'で済ませてしまう。
item_dict['common'] = {}
item_dict['common'] = set_data_for_product('common', 
                                           df_dict, 
                                           params['data_attributes'], 
                                           item_dict_by_product=item_dict['common'], 
                                           item_dict_common=item_dict['common'])

'''product_list = ['prod_01', 'prod_02']

for product in product_list:
    item_dict[product] = {}
    item_dict[product] = set_data_for_product(product, df_dict, data_attributes, item_dict_by_product=item_dict[product], item_dict_common=item_dict['common'])
'''
#item_dict = set_data_single_prod(df_dict, data_attributes=data_attributes, item_dict=item_dict)
import pprint

pprint.pprint(item_dict)

import lispy as lp

#-----------------------------------------------
li = lp.LispInterpreter()
li.env |= item_dict['common']
li.interpret(f'(begin{lisp})')
FCF = li.interpret('FCF')

import matplotlib.pyplot as plt

plt.plot(range(45), FCF)
plt.show()


'''li = {}
for prod in product_list:
    li[prod] = lp.LispInterpreter()
    li[prod].env |= item_dict['common']
    li[prod].env |= item_dict[prod]

    li[prod].interpret(f'(begin{lisp})')
    FCF = li[prod].interpret('FCF')

    import matplotlib.pyplot as plt

    plt.plot(range(45), FCF)
    plt.show()
'''

