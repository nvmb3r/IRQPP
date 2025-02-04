#!/usr/bin/env python

import argparse
from collections import defaultdict

import pandas as pd
# import xml.etree.ElementTree as etree
from lxml import etree as etree

parser = argparse.ArgumentParser(description='Adding fbDocs to queries xml file',
                                 usage='Receives a query xml file and trec results file',
                                 epilog='Adds the K first documents to each query as feedback')

parser.add_argument('-r', '--results', metavar='results_file', default='baseline/QL.res',
                    help='The results file for the Relevance Feedback')
parser.add_argument('-q', '--queries', metavar='queries_xml_file', default='data/ROBUST/queries.xml',
                    help='The queries xml file')
parser.add_argument('-d', '--docs', metavar='fbDocs', type=int, default=2, help='Number of Feedback documents to add')


class QueriesParser:
    def __init__(self, query_file):
        self.file = query_file
        _parser = etree.XMLParser(remove_blank_text=True)
        self.tree = etree.parse(self.file, _parser)
        self.root = self.tree.getroot()
        # query number: "Full command"
        self.full_queries = defaultdict(str)
        self.fb_docs = defaultdict(list)
        self.__parse_queries()

    def __parse_queries(self):
        for query in self.root.iter('query'):
            self.full_queries[query.find('number').text] = query.find('text').text

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
                temp = etree.SubElement(query, 'feedbackDocno')
                temp.text = doc
        # etree.dump(self.tree)
        print(etree.tostring(self.tree, pretty_print=True, encoding='unicode'))


def main(args):
    results_file = args.results
    query_file = args.queries
    number_of_docs = args.docs
    results_df = pd.read_table(results_file, delim_whitespace=True, header=None, index_col=[0, 3],
                               names=['qid', 'Q0', 'docID', 'docRank', 'docScore', 'ind'],
                               dtype={'qid': str, 'Q0': str, 'docID': str, 'docRank': int, 'docScore': float,
                                      'ind': str})

    qdb = QueriesParser(query_file)
    qdb.add_feedback_docs(number_of_docs, results_df)
    qdb.write_to_file()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
