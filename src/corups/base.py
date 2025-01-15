import os
import json
import random
from typing import *

import numpy as np
import pandas as pd

from pandasql import sqldf
from pandas.api.types import is_integer_dtype, is_bool_dtype, is_float_dtype, is_datetime64_dtype, is_object_dtype, is_categorical_dtype
# from sentence_transformers import SentenceTransformer
# import torch

from src.utils import raise_error

_REQUIRED_COLUMNS = ['id', 'title']


def _pd_type_to_sql_type(col: pd.Series) -> str:
    res = ''
    if is_integer_dtype(col):
        res = 'integer'
    elif is_float_dtype(col):
        res = 'float'
    elif is_bool_dtype(col):
        res = 'boolean'
    elif is_datetime64_dtype(col):
        res = 'datetime'
    elif is_object_dtype(col) or is_categorical_dtype(col):
        res = 'string'
    else:
        res = 'string'
    return res


class BaseGallery:
    def __init__(self, fpath: str, resource_setting: dict, sep: str=',', parquet_engine: str='pyarrow') -> None:
        self.fpath = fpath
        self.corups, self.column_meaning, categorical_cols, self.domain_desc = self._read_file(fpath, resource_setting, sep, parquet_engine)
        
        self.disp_cate_topk: int = 10
        self.disp_cate_total: int = 20
        self._fuzzy_bert_base = "thenlper/gte-base" 

        self.categorical_col_values = {}
        for domain in categorical_cols:
            self.categorical_col_values[domain] = {}
            for col in categorical_cols[domain]:
                _explode_df = self.corups[domain].explode(col)[col]
                self.categorical_col_values[domain][col] = _explode_df[~ _explode_df.isna()].unique()
                # if isinstance(self.corups[domain][col][0], str) or self.corups[domain][col].dtype == bool:
                #     pass
                # else:
                #     self.corups[domain][col] = self.corups[domain][col].apply(lambda x: ', '.join(x))

        # if torch.cuda.is_available():
        #     device = 'cuda'
        # else:
        #     device = 'cpu'
        # _fuzzy_bert_engine = SentenceTransformer(self._fuzzy_bert_base, device=device)
        # self.fuzzy_engine: Dict[str, SentBERTEngine] = {
        #     col: SentBERTEngine(
        #         self.corups[col].to_numpy(),
        #         self.corups["id"].to_numpy(),
        #         case_sensitive=False,
        #         model=_fuzzy_bert_engine
        #     )
        #     if col not in categorical_cols
        #     else SentBERTEngine(
        #         self.categorical_col_values[col],
        #         np.arange(len(self.categorical_col_values[col])),
        #         case_sensitive=False,
        #         model=_fuzzy_bert_engine
        #     )
        #     for col in fuzzy_cols
        # }
        # self.fuzzy_engine['sql_cols'] = SentBERTEngine(
        #     np.array(columns), 
        #     np.arange(len(columns)),
        #     case_sensitive=False,
        #     model=_fuzzy_bert_engine
        # )   # fuzzy engine for column names
        # name as index
        for domain in self.corups:
            if domain == 'train':
                self.corups[domain].set_index('trainID', drop=True, inplace=True)
            else:
                self.corups[domain].set_index('id', drop=True, inplace=True)


    def __call__(self, sql: str, corups: pd.DataFrame=None, return_id_only: bool=False) -> List:
        """Search in corups with SQL query
        
        Args:
            sql: A sql query command.

        Returns:
            list: the result represents by id
        """
        if corups is None:
            result = sqldf(sql, self.corups)    # all items
        else:
            raise_error(Exception, 'not implemented')
            result = sqldf(sql, {self.name: corups})   # items in buffer

        if return_id_only:
            raise_error(Exception, 'not implemented')
            result = result[self.corups.index.name].to_list()
        return result


    def __len__(self) -> int:
        return len(self.corups)
    
    def info(self, query: str=None):
        res = []
        for domain in self.corups:
            res.append(self.domain_info(domain))
        return '\n\n'.join(res)

    def domain_info(self, domain, remove_item_titles: bool=False, query: str=None):
        prefix = 'Table information:'
        table_name = f"Table Name: {domain}"
        table_desc = f"Table Desc: {self.domain_desc[domain]}"
        cols_info = "Column Names, Data Types and Column meaning:"
        cols_info += f"\n    - {self.corups[domain].index.name}({_pd_type_to_sql_type(self.corups[domain].index)}): {self.column_meaning[domain][self.corups[domain].index.name]}"
        for col in self.corups[domain].columns:
            if remove_item_titles and 'title' in col:
                continue
            dtype = _pd_type_to_sql_type(self.corups[domain][col])
            cols_info += f"\n    - {col}({dtype}): {self.column_meaning[domain][col]}"
            if col in self.categorical_col_values[domain]:
                disp_values = self.sample_categoricol_values(domain, col, total_n=self.disp_cate_total, query=query, topk=self.disp_cate_topk)
                _prefix = f" Related values: [{', '.join(sorted(disp_values))}]."
                cols_info += _prefix

            if dtype in {'float', 'datetime', 'integer'}:
                _min = self.corups[domain][col].min()
                _max = self.corups[domain][col].max()
                _mean = self.corups[domain][col].mean()
                _median = self.corups[domain][col].median()
                _prefix = f" Value ranges from {_min} to {_max}. The average value is {_mean}. The median is {_median}."
                cols_info += _prefix

        primary_key = f"Primary Key: {self.corups[domain].index.name}"
        categorical_cols = list(self.categorical_col_values[domain].keys())
        note = f"Note that [{','.join(categorical_cols)}] columns are categorical, must use related values to search otherwise no result would be returned."
        res = ''
        for i, s in enumerate([table_name, table_desc, cols_info, primary_key, note]):
            res += f"\n{i}. {s}"
        res = prefix + res
        return res

    def sample_categoricol_values(self, domain, col_name: str, total_n: int, query: str=None, topk: int=None) -> List:
        # Select topk related tags according to query and sample (total_n-topk) tags
        if query is None or col_name not in self.fuzzy_engine:
            result = random.sample(list(self.categorical_col_values[domain][col_name]), k=min(len(self.categorical_col_values[domain][col_name]), total_n))
        else:
            raise_error(Exception, 'not impeleted')
            # if topk is None:
            #     topk = total_n
            # topk = min(len(self.categorical_col_values[domain][col_name]), topk)
            # assert total_n >= topk, f"`topk` must be smaller than `total_n`, while got {topk} > {total_n}."
            # topk_values = self.fuzzy_engine[col_name](query, return_doc=True, topk=topk)
            # topk_values = list(topk_values)
            # result = topk_values
            # if total_n > topk:
            #     while (len(result) < total_n) and (len(result) < len(self.categorical_col_values[domain][col_name])):
            #         random_values = random.choice(self.categorical_col_values[domain][col_name])
            #         if random_values not in result:
            #             result.append(random_values)
        return result


    def convert_id_2_info(self, item_id: Union[int, List[int], np.ndarray], col_names: Union[str, List[str]]=None) -> Union[Dict, List[Dict]]:
        """Given item_id, get item informations.
        
        Args:
            - item_id: item ids. 
            - col_names: column names to be returned

        Returns:
            - information of given item ids, each item is formatted as a dict, whose key is column name.
        
        """
        if col_names is None:
            col_names = self.corups.columns
        else:
            if isinstance(col_names, str):
                col_names = [col_names]
            elif isinstance(col_names, list):
                pass
            else:
                raise_error(TypeError, "Not supported type for `col_names`.")

        if isinstance(item_id, int):
            items = self.corups.loc[item_id][col_names].to_dict()
        elif isinstance(item_id, list) or isinstance(item_id, np.ndarray):
            items = self.corups.loc[item_id][col_names].to_dict(orient='list')
        else:
            raise_error(TypeError, "Not supported type for `item_id`.")

        return items


    def convert_title_2_info(self, titles: Union[int, List[int], np.ndarray], col_names: Union[str, List[str]]=None) -> Union[Dict, List[Dict]]:
        """Given item title, get item informations.
        
        Args:
            - titles: item titles. Note that the item title must exist in the table. 
            - col_names: column names to be returned

        Returns:
            - information of given item titles, each item is formatted as a dict, whose key is column name.
        
        """
        if col_names is None:
            col_names = self.corups_title.columns
        else:
            if isinstance(col_names, str):
                col_names = [col_names]
            elif isinstance(col_names, list):
                pass
            else:
                raise_error(TypeError, "Not supported type for `col_names`.")

        if isinstance(titles, str) or (isinstance(titles, np.ndarray) and len(titles.shape)==0):
            items = self.corups_title.loc[titles][col_names].to_dict()
        elif isinstance(titles, list) or (isinstance(titles, np.ndarray) and len(titles.shape)>0):
            items = self.corups_title.loc[titles][col_names].to_dict(orient='list')
        else:
            raise_error(TypeError, "Not supported type for `titles`.")

        return items


    def _read_file(self, fpath: str, resource_setting: dict, sep: str=',', parquet_engine: str='pyarrow') -> pd.DataFrame:
        corups = {}
        column_meaning = {}
        categorical_cols = {}
        domain_desc = {}
        for domain in resource_setting:
            columns = resource_setting[domain]['USE_COLS']
            resource_path = os.path.join(fpath, domain, resource_setting[domain]['INFO_FILE'])
            col_des_path = os.path.join(fpath, domain, resource_setting[domain]['TABLE_COL_DESC_FILE'])
            domain_desc[domain] = resource_setting[domain]['TABLE_DESC']
            if resource_path.endswith('.csv') or resource_path.endswith('.tsv'):
                df = pd.read_csv(resource_path, sep=sep, names=columns)
            elif resource_path.endswith('.ftr'):
                df = pd.read_feather(resource_path)
            elif resource_path.endswith('.parquet'):
                df = pd.read_parquet(resource_path, engine=parquet_engine)
            elif resource_path.endswith('.json'):
                df = pd.read_json(resource_path)
            else:
                raise_error(TypeError, "Not support for such file type now.")
            
            if columns is not None:
                df = df[columns]
            
            for c in columns:
                if is_integer_dtype(df[c]):
                    df[c] = df[c].astype(str)
                elif is_float_dtype(df[c]):
                    df[c] = df[c].astype('Int64')
                    df[c] = df[c].astype(str)
            
            # delete space
            df.columns = [c.replace(' ', '') for c in df.columns]
            c_meaning = self._load_col_desc_file(col_des_path)
            for c in list(c_meaning.keys()):
                c_meaning[c.replace(' ', '')] = c_meaning[c]
                            
            corups[domain] = df
            column_meaning[domain] = c_meaning
            categorical_cols[domain] = resource_setting[domain]['CATEGORICAL_COLS']
            print(f"Columns in item corups: {df.columns}.")
        return corups, column_meaning, categorical_cols, domain_desc


    def _load_col_desc_file(self, fpath: str) -> Dict:
        assert fpath.endswith('.json'), "Only support json file now."
        with open(fpath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def fuzzy_match(self, value: Union[str, List[str]], col: str) -> Union[str, List[str]]:
        if col not in self.fuzzy_engine:
            raise_error(ValueError, f"Not support fuzzy search for column {col}")
        else:
            res = self.fuzzy_engine[col](value, return_doc=True, topk=1) 
            res = np.squeeze(res, axis=-1)
            return res
