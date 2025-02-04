#!/usr/bin/env python

import argparse
from collections import defaultdict

import numpy as np
import pandas as pd

from qpputils.dataparser import ResultsReader

parser = argparse.ArgumentParser(description='UQV aggregated queries calculations script',
                                 usage='python3.6 aggregateUQV.py RAW_AP_FILE RAW_PREDICTIONS_FILE -f FUNCTION',
                                 epilog='Calculate new UQV scores')

parser.add_argument('-m', '--map', metavar='RAW_AP_FILE', help='path to raw ap scores file')
parser.add_argument('-p', '--predictions', metavar='RAW_PREDICTIONS_FILE', help='path to raw predictions file')
parser.add_argument('-f', '--function', type=str, default='avg', choices=['max', 'std', 'min', 'avg', 'med'],
                    help='Aggregate function')


# TODO: the uef predictions for 5 and 10 documents yield results with var=0, it returns NAN for pearson correlation


class Aggregate:
    def __init__(self, data_df: pd.DataFrame, agg_func):
        self.data = data_df
        self.agg_func = agg_func
        self.agg_scores_dict = self._aggregate_scores()
        self.final_score_dict = self._calc_scores()

    def _aggregate_scores(self):
        _agg = defaultdict(list)
        for qid, _score in self.data.itertuples():
            qid = qid.split('-')[0]
            _agg[qid].append(_score)
        return _agg

    def _calc_scores(self):
        _final_scores = defaultdict(float)
        for qid, scores in self.agg_scores_dict.items():
            if self.agg_func.lower() == 'max':
                score = np.max(scores)
            elif self.agg_func.lower() == 'min':
                score = np.min(scores)
            elif self.agg_func.lower() == 'avg':
                score = np.mean(scores)
            elif self.agg_func.lower() == 'std':
                score = np.std(scores)
            elif self.agg_func.lower() == 'med':
                score = np.median(scores)
            else:
                assert False, 'Unknown aggregate function {}'.format(self.agg_func)
            _final_scores[qid] = score
        return _final_scores

    def print_score(self):
        for qid, score in self.final_score_dict.items():
            print('{} {}'.format(qid, score))


def main(args: parser):
    map_file = args.map
    predictions_file = args.predictions
    agg_func = args.function

    # # Debugging - should be in comment when not debugging !
    # print('\n------+++^+++------ Debugging !! ------+++^+++------\n')
    # predictions_file = '/home/olegzendel/QppUqvProj/Results/ROBUST/uqvPredictions/raw/preret/AvgVarTFIDF/predictions/predictions-AvgVarTFIDF'
    # agg_func = 'max'

    assert not (map_file is None and predictions_file is None), 'No file was given'

    if map_file is not None:
        ap_scores = ResultsReader(map_file, 'ap')
        aggregation = Aggregate(ap_scores.data_df, agg_func)
        aggregation.print_score()
    else:
        prediction_scores = ResultsReader(predictions_file, 'predictions')
        agg_prediction = Aggregate(prediction_scores.data_df, agg_func)
        agg_prediction.print_score()


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
