import dataparser as dp
from itertools import combinations
from collections import defaultdict
from RBO import rbo_dict
import pandas as pd
import numpy as np
import os

import argparse
from Timer.timer import Timer

parser = argparse.ArgumentParser(description='Features for UQV query variations Generator',
                                 usage='python3.6 features.py -q queries.txt -c CORPUS -r QL.res ',
                                 epilog='Unless --generate is given, will try loading the file')

parser.add_argument('-q', '--queries', metavar='queries.txt', help='path to UQV queries txt file')
parser.add_argument('-c', '--corpus', default='ROBUST', type=str, help='corpus (index) to work with',
                    choices=['ROBUST', 'ClueWeb12B'])
parser.add_argument('-r', '--results', default=None, type=str, help='QL.res file of the queries')
parser.add_argument('-f', '--fused', default=None, type=str, help='fusedQL.res file of the queries')
parser.add_argument('-l', '--load', default=None, type=str, help='features file to load')

parser.add_argument('--generate', help="generate new predictions", action="store_true")


class QueryFeatureFactory:
    def __init__(self, corpus):
        self.__set_paths(corpus)
        self.raw_res_data = dp.ResultsReader(self.results_file, 'trec')
        self.title_res_data = dp.ResultsReader(self.title_res_file, 'trec')
        self.queries_data = dp.QueriesTextParser(self.queries_full_file, 'uqv')
        self.topics_data = dp.QueriesTextParser(self.queries_topic_file)
        # A simple sanity check to make sure number of results and query variations is identical
        _x = [len(i) for i in self.raw_res_data.query_vars.values()]
        _z = [len(i) for i in self.queries_data.query_vars.values()]
        assert _x == _z, 'Results and Queries files don\'t match'
        self.fused_data = dp.ResultsReader(self.fused_results_file, 'trec')
        self.query_vars = self.queries_data.query_vars

    # def _create_query_var_pairs(self):
    #     feature_keys = defaultdict(list)
    #     for qid, variations in self.query_vars.items():
    #         feature_keys[qid] = list(combinations(variations, 2))
    #     return feature_keys

    @classmethod
    def __set_paths(cls, corpus):
        """This method sets the default paths of the files and the working directories, it assumes the standard naming
         convention of the project"""
        # cls.predictor = predictor
        _results_file = f'~/QppUqvProj/Results/{corpus}/test/raw/QL.res'
        cls.results_file = os.path.normpath(os.path.expanduser(_results_file))
        dp.ensure_file(cls.results_file)

        _title_results_file = f'~/QppUqvProj/Results/{corpus}/test/basic/QL.res'
        cls.title_res_file = os.path.normpath(os.path.expanduser(_title_results_file))
        dp.ensure_file(cls.title_res_file)

        _queries_full_file = f'~/QppUqvProj/data/{corpus}/queries_{corpus}_UQV_full.txt'
        cls.queries_full_file = os.path.normpath(os.path.expanduser(_queries_full_file))
        dp.ensure_file(cls.queries_full_file)

        _queries_topic_file = f'~/QppUqvProj/data/{corpus}/queries_{corpus}_title.txt'
        cls.queries_topic_file = os.path.normpath(os.path.expanduser(_queries_topic_file))
        dp.ensure_file(cls.queries_topic_file)

        _fused_results_file = f'~/QppUqvProj/Results/{corpus}/test/fusion/QL.res'
        cls.fused_results_file = os.path.normpath(os.path.expanduser(_fused_results_file))
        dp.ensure_file(cls.fused_results_file)

        cls.output_dir = f'~/QppUqvProj/Results/{corpus}/test/raw/'
        dp.ensure_dir(cls.output_dir)

    def _calc_features(self):
        _dict = {'topic': [], 'qid': [], 'Jac_coefficient': [], 'Top_10_Docs_overlap': [], 'RBO_EXT_100': [],
                 'RBO_FUSED_EXT_100': []}

        for topic in self.topics_data.queries_dict.keys():
            q_vars = self.query_vars.get(topic)
            _dict['topic'] += [topic] * len(q_vars)
            dt_100 = self.fused_data.get_res_dict_by_qid(topic, top=100)
            topic_txt = self.topics_data.get_qid_txt(topic)
            topics_top_list = self.title_res_data.get_docs_by_qid(topic, 10)
            topic_results_list = self.title_res_data.get_res_dict_by_qid(topic, top=100)

            for var in q_vars:
                var_txt = self.queries_data.get_qid_txt(var)
                jc = self.jaccard_coefficient(topic_txt, var_txt)

                var_top_list = self.raw_res_data.get_docs_by_qid(var, 10)
                docs_overlap = self.list_overlap(topics_top_list, var_top_list)

                # All RBO values are rounded to 10 decimal digits, to avoid float overflow
                var_results_list = self.raw_res_data.get_res_dict_by_qid(var, top=100)
                _rbo_scores_100 = rbo_dict(topic_results_list, var_results_list, p=0.95)
                _ext_100 = np.around(_rbo_scores_100['ext'], 10)

                _fused_rbo_scores_100 = rbo_dict(dt_100, var_results_list, p=0.95)
                _var_fext_100 = np.around(_fused_rbo_scores_100['ext'], 10)

                _dict['qid'] += [var]
                _dict['Jac_coefficient'] += [jc]
                _dict['Top_10_Docs_overlap'] += [docs_overlap]
                _dict['RBO_EXT_100'] += [_ext_100]
                _dict['RBO_FUSED_EXT_100'] += [_var_fext_100]

        _df = pd.DataFrame.from_dict(_dict)
        _df.set_index(['topic', 'qid'], inplace=True)
        return _df

    def _sum_scores(self, df):
        # _exp_df = df.apply(np.exp)
        # For debugging purposes
        # df.to_excel(self.writer, 'normal_scores')
        # _exp_df.to_excel(self.writer, 'exp_scores')

        z_n = df.groupby(['topic']).sum()
        # z_e = _exp_df.groupby(['topic']).sum()

        norm_df = (df.groupby(['topic', 'qid']).sum() / z_n)
        # softmax_df = (_exp_df.groupby(['topic', 'qid']).sum() / z_e)
        # For debugging purposes
        # norm_df.to_excel(self.writer, 'zn_scores')
        # softmax_df.to_excel(self.writer, 'ze_scores')
        # self.writer.save()
        return norm_df

    def generate_features(self):
        _df = self._calc_features()
        return self._sum_scores(_df)

    @staticmethod
    def jaccard_coefficient(st1: str, st2: str):
        st1_set = set(st1.split())
        st2_set = set(st2.split())
        union = st1_set.union(st2_set)
        intersect = st1_set.intersection(st2_set)
        return float(len(intersect) / len(union))

    @staticmethod
    def list_overlap(x, y):
        x_set = set(x)
        intersection = x_set.intersection(y)
        return len(intersection)


def features_loader(file_to_load, corpus):
    if file_to_load is None:
        file = dp.ensure_file('features_{}_uqv.JSON'.format(corpus))
    else:
        file = dp.ensure_file(file_to_load)

    features_df = pd.read_json(file, dtype={'topic': str, 'qid': str})
    features_df.reset_index(drop=True, inplace=True)
    features_df.set_index(['topic', 'qid'], inplace=True)
    features_df.sort_values(['topic', 'qid'], axis=0, inplace=True)
    return features_df


def main(args):
    queries_file = args.queries
    corpus = args.corpus
    results_file = args.results
    fused_res_file = args.fused
    file_to_load = args.load
    generate = args.generate

    # assert not queries_file.endswith('.xml'), 'Submit text queries file, not XML'

    if generate:
        # queries_file = dp.ensure_file(queries_file)
        # results_file = dp.ensure_file(results_file)
        testing_feat = QueryFeatureFactory(corpus)
        norm_features_df = testing_feat.generate_features()
        norm_features_df.reset_index().to_json('query_features_{}_uqv.JSON'.format(corpus))
    else:
        features_df = features_loader(file_to_load, corpus)
        print(features_df)


if __name__ == '__main__':
    args = parser.parse_args()
    overall_timer = Timer('Total runtime')
    main(args)
    overall_timer.stop()
