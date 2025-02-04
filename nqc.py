#! /usr/bin/env python

import argparse
import xml.etree.ElementTree as eT
from collections import defaultdict

import numpy as np
import pandas as pd

# TODO: remove the queries file, or implement an option to add it just for testing (ensure all queries are present)
# TODO: switch the code to work with the global qpputils

parser = argparse.ArgumentParser(description='NQC predictor',
                                 usage='Input QL(q|d) scores and queries files',
                                 epilog='Prints the NQC predictor scores')

parser.add_argument('results', metavar='QL(q|d)_results_file', help='The QL results file for the documents scores')
parser.add_argument('corp_scores', metavar='QLC', help='logqlc QL Corpus scores of the queries')
parser.add_argument('queries', metavar='queries_xml_file', default='data/ROBUST/queries.xml',
                    help='The queries xml file')
parser.add_argument('-t', '--textqueries', metavar='queries_txt_file', default='data/ROBUST/queries.txt',
                    help='The queries txt file')
parser.add_argument('-d', '--docs', metavar='fbDocs', default=20, help='Number of documents')


class QueriesParser:
    def __init__(self, query_file):
        self.file = query_file
        self.tree = eT.parse(self.file)
        self.root = self.tree.getroot()
        # query number: "Full command"
        self.full_queries = defaultdict(str)
        self.text_queries = defaultdict(str)
        self.query_length = defaultdict(int)
        self.fb_docs = defaultdict(list)
        self.__parse_queries()

    def __parse_queries(self):
        for query in self.root.iter('query'):
            qid_ = query.find('number').text
            qstr_ = query.find('text').text
            qtxt_ = qstr_[qstr_.find("(") + 1:qstr_.rfind(")")].split()
            self.full_queries[qid_] = qstr_
            self.text_queries[qid_] = qtxt_
            self.query_length[qid_] = len(qtxt_)

    def add_feedback_docs(self, num_docs, res):
        """
        Adds the fbDocs from results file to the original queries
        :parameter: num_files: number of fbDocs to add to each query
        """
        for qid in self.full_queries.keys():
            qid = qid
            docs = res.loc[qid]['docID'].head(num_docs)
            self.fb_docs[qid] = list(docs)

    def write_to_file(self):
        for query in self.root.iter('query'):
            qid = query.find('number').text
            fbDocs = self.fb_docs[qid]
            for doc in fbDocs:
                temp = eT.SubElement(query, 'feedbackDocno')
                temp.text = doc
        eT.dump(self.tree)


class NQC:
    """This class implements the QPP method as described in:
    'Predicting Query Performance by Query-Drift Estimation'
    The predictor is implemented to work with log(QL) scores (not -CE)"""

    def __init__(self, queries_obj, results_df, corpus_scores_df):
        self.qdb = queries_obj
        self.res = results_df
        self.corp = corpus_scores_df
        self.predictions = defaultdict(float)

    def _calc_denominator(self, qid):
        _score = self.corp.loc[qid]['score']
        return abs(_score)

    def _calc_numerator(self, qid, num_docs):
        _scores = list(self.res.loc[qid]['docScore'].head(num_docs))
        for i, score in enumerate(_scores):
            _scores[i] = score
        return np.std(_scores)

    # Version for -CE scores
    # def _calc_numerator(self, qid, qlen, num_docs):
    #     _scores = list(self.res.loc[qid]['docScore'].head(num_docs))
    #     for i, score in enumerate(_scores):
    #         _scores[i] = score * qlen
    #     return np.std(_scores)

    def calc_results(self, number_of_docs):
        for qid, qlen in self.qdb.query_length.items():
            _denominator = self._calc_denominator(qid)
            _numerator = self._calc_numerator(qid, number_of_docs)
            _score = _numerator / _denominator
            self.predictions[qid] = _score
            print('{} {:0.4f}'.format(qid, _score))
        # predictions_df = pd.Series(self.predictions)
        # predictions_df.to_json('wig-predictions-{}.res'.format(number_of_docs))


def main(args):
    results_file = args.results
    query_file = args.queries
    number_of_docs = int(args.docs)
    logqlc_file = args.corp_scores
    corp_scores_df = pd.read_table(logqlc_file, delim_whitespace=True, header=None, index_col=0, names=['qid', 'score'],
                                   dtype={'qid': str, 'score': float})
    results_df = pd.read_table(results_file, delim_whitespace=True, header=None, index_col=0,
                               names=['qid', 'Q0', 'docID', 'docRank', 'docScore', 'ind'],
                               dtype={'qid': str, 'Q0': str, 'docID': str, 'docRank': int, 'docScore': float,
                                      'ind': str})
    results_df.index = results_df.index.map(str)
    corp_scores_df.index = corp_scores_df.index.map(str)
    qdb = QueriesParser(query_file)
    nqc = NQC(qdb, results_df, corp_scores_df)
    nqc.calc_results(number_of_docs)


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
