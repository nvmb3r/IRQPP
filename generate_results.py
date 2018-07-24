#!/usr/bin/env python

import argparse
import multiprocessing
import os
from subprocess import run

from Timer.timer import Timer

# TODO: Add directories checks and creation
# os.path.exists('file or dir')
# os.path.isfile('file')
# os.path.isdir('dir')
# TODO: Create for UQV aggregations

# TODO: Create for UQV singles
# TODO: Create CV process and write the results to tables
# TODO: Add a check that all necessary files exist on startup (to avoid later crash)

PREDICTORS = ['clarity', 'nqc', 'wig', 'qf']
NUM_DOCS = [5, 10, 25, 50, 100, 250, 500, 1000]
LIST_CUT_OFF = [5, 10, 25, 50, 100]
AGGREGATE_FUNCTIONS = ['max', 'std', 'min', 'avg', 'med']
SINGLE_FUNCTIONS = ['max', 'min', 'medl', 'medh']

parser = argparse.ArgumentParser(description='Full Results Pipeline Automation Generator',
                                 usage='Run / Load Results and generate table in LateX',
                                 epilog='Currently Beta Version')

parser.add_argument('--predictor', metavar='predictor_name', help='predictor to run',
                    choices=['clarity', 'wig', 'nqc', 'qf', 'uef', 'all'])
# parser.add_argument('-r', '--predictions_dir', metavar='results_dir_path',
#                     default='~/QppUqvProj/Results/ROBUST/basicPredictions/', help='path where to save results')
parser.add_argument('-q', '--queries', metavar='queries.xml', default='~/data/ROBUST/queries.xml',
                    help='path to queries xml res')
parser.add_argument('-c', '--corpus', default='ROBUST', type=str, help='corpus (index) to work with',
                    choices=['ROBUST', 'ClueWeb12B'])
parser.add_argument('--qtype', default='basic', type=str, help='The type of queries to run',
                    choices=['basic', 'single', 'aggregated'])
parser.add_argument('--generate', help="generate new predictions", action="store_true")


class GeneratePredictions:
    def __init__(self, queries, predictions_dir, corpus='ROBUST', qtype='basic'):
        """
        :param queries: queries XML file
        :param predictions_dir: default predictions results dir
        """
        self.queries = queries
        self.predictions_dir = os.path.normpath(os.path.expanduser(predictions_dir)) + '/'
        self.corpus = corpus
        self.qtype = qtype
        self.cpu_cores = max(multiprocessing.cpu_count() * 0.5, min(multiprocessing.cpu_count() - 1, 16))

    @staticmethod
    def __run_indri_app(predictor_exe, parameters, threads, running_param, n, queries, output):
        ensure_dir(output)
        run('{} {} {} {}{} {} > {}'.format(predictor_exe, parameters, threads, running_param, n, queries, output),
            shell=True)

    @staticmethod
    def __run_py_predictor(predictor_exe, parameters, temporal_var, running_param, n, output):
        ensure_dir(output)
        run('{} {} {} {}{} > {}'.format(predictor_exe, parameters, temporal_var, running_param, n, output), shell=True)

    def __run_predictor(self, predictions_dir, predictor_exe, parameters, running_param, lists=False, queries=None):
        threads = '-threads={}'.format(self.cpu_cores)
        if queries is None:
            queries = self.queries
        if lists:
            res = 'list'
            print('\n ******** Generating Lists ******** \n')
        else:
            res = 'predictions'
            print('\n ******** Generating Predictions ******** \n')

        if 'indri' in predictor_exe.lower():
            # Running indri APP
            _queries = queries
            for n in NUM_DOCS:
                print('\n ******** Running for: {} documents ******** \n'.format(n))
                output = predictions_dir + '{}-{}'.format(res, n)
                if 'uef' in queries.lower():
                    # Assuming it's uef lists creation
                    queries = '{}-{}.xml'.format(_queries, n)
                ensure_files([predictor_exe, parameters, queries])
                self.__run_indri_app(predictor_exe, parameters, threads, running_param, n, queries, output)

        elif predictor_exe.endswith('qf.py'):
            lists_dir = predictions_dir.replace('predictions', 'lists')
            for n in NUM_DOCS:
                for k in LIST_CUT_OFF:
                    print('\n ******** Running for: {} documents + {} list cutoff ******** \n'.format(n, k))
                    output = predictions_dir + '{}-{}+{}'.format(res, n, k)
                    inlist = lists_dir + 'list-{}'.format(n)
                    ensure_files([predictor_exe.split()[1]] + [parameters, inlist])
                    self.__run_py_predictor(predictor_exe, parameters, inlist, running_param, k, output)

        elif predictor_exe.endswith('addWorkingsetdocs.py'):
            print('\n ******** Generating UEF query files ******** \n')
            for n in NUM_DOCS:
                output = predictions_dir + 'queriesUEF-{}.xml'.format(n)
                ensure_files([predictor_exe.split()[1]] + [parameters, queries])
                self.__run_py_predictor(predictor_exe, parameters, queries, running_param, n, output)

        elif predictor_exe.endswith(('nqc.py', 'wig.py')):
            for n in NUM_DOCS:
                print('\n ******** Running for: {} documents ******** \n'.format(n))
                output = predictions_dir + '{}-{}'.format(res, n)
                ensure_files([predictor_exe.split()[1]] + [parameters, queries])
                self.__run_py_predictor(predictor_exe, parameters, queries, running_param, n, output)

        elif predictor_exe.endswith('uef.py'):
            lists_dir = predictions_dir + 'lists/'
            for pred in PREDICTORS:
                for n in NUM_DOCS:
                    if pred != 'qf':
                        print('\n ******** Running for: {} documents ******** \n'.format(n))
                        output = predictions_dir + '{}/predictions/{}-{}'.format(pred, res, n)
                        inlist = lists_dir + 'list-{}'.format(n)
                        predictions = predictions_dir.replace('uef', pred) + 'predictions/{}-{}'.format(res, n)
                        params = '{} {}'.format(inlist, predictions)
                        ensure_files([predictor_exe.split()[1]] + [parameters, inlist, predictions])
                        self.__run_py_predictor(predictor_exe, parameters, params, running_param, n, output)
                    else:
                        for k in LIST_CUT_OFF:
                            print('\n ******** Running for: {} documents + {} list cutoff ******** \n'.format(n, k))
                            output = predictions_dir + '{}/predictions/{}-{}+{}'.format(pred, res, n, k)
                            inlist = lists_dir + 'list-{}'.format(n)
                            predictions = predictions_dir.replace('uef', pred)
                            predictions += 'predictions/{}-{}+{}'.format(res, n, k)
                            params = '{} {}'.format(inlist, predictions)
                            ensure_files([predictor_exe.split()[1]] + [parameters, inlist, predictions])
                            self.__run_py_predictor(predictor_exe, parameters, params, running_param, n, output)

    def generate_clartiy(self, predictions_dir=None):
        print('\n -- Clarity -- \n')
        predictor_exe = '~/SetupFiles-indri-5.6/clarity.m-2/Clarity-Anna'
        parameters = '~/QppUqvProj/Results/{}/test/clarityParam.xml'.format(self.corpus)
        running_param = '-fbDocs='
        if predictions_dir is None:
            predictions_dir = self.predictions_dir + 'clarity/predictions/'
        else:
            predictions_dir = predictions_dir + 'clarity/predictions/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)

    def generate_wig(self, predictions_dir=None):
        print('\n -- WIG -- \n')
        predictor_exe = 'python3.6 ~/repos/IRQPP/wig.py'
        ql_scores = '~/QppUqvProj/Results/{}/test/{}/QL.res'.format(self.corpus, self.qtype)
        qlc_scores = '~/QppUqvProj/Results/{}/test/{}/logqlc.res'.format(self.corpus, self.qtype)
        parameters = '{} {}'.format(ql_scores, qlc_scores)
        running_param = '-d '
        if predictions_dir is None:
            predictions_dir = self.predictions_dir + 'wig/predictions/'
        else:
            predictions_dir = predictions_dir + 'wig/predictions/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)

    def generate_nqc(self, predictions_dir=None):
        print('\n -- NQC -- \n')
        predictor_exe = 'python3.6 ~/repos/IRQPP/nqc.py'
        ql_scores = '~/QppUqvProj/Results/{}/test/{}/QL.res'.format(self.corpus, self.qtype)
        qlc_scores = '~/QppUqvProj/Results/{}/test/{}/logqlc.res'.format(self.corpus, self.qtype)
        parameters = '{} {}'.format(ql_scores, qlc_scores)
        running_param = '-d '
        if predictions_dir is None:
            predictions_dir = self.predictions_dir + 'nqc/predictions/'
        else:
            predictions_dir = predictions_dir + 'nqc/predictions/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)

    def generate_qf(self, predictions_dir=None):
        print('\n -- QF -- \n')
        self._generate_lists_qf()
        predictor_exe = 'python3.6 ~/repos/IRQPP/qf.py'
        parameters = '~/QppUqvProj/Results/{}/test/{}/QL.res'.format(self.corpus, self.qtype)
        running_param = '-d '
        if predictions_dir is None:
            predictions_dir = self.predictions_dir + 'qf/predictions/'
        else:
            predictions_dir = predictions_dir + 'qf/predictions/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)

    def _generate_lists_qf(self):
        predictor_exe = '~/SetupFiles-indri-5.6/runqueryql/IndriRunQueryQL'
        parameters = '~/QppUqvProj/Results/{}/test/indriRunQF.xml'.format(self.corpus)
        running_param = '-fbDocs='
        predictions_dir = self.predictions_dir + 'qf/lists/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param, lists=True)

    def generate_uef(self):
        """Assuming all the previous predictions exist, will generate the uef lists and predictions"""
        self._generate_lists_uef()
        predictor_exe = 'python3.6 ~/repos/IRQPP/uef/uef.py'
        parameters = '~/QppUqvProj/Results/{}/test/{}/QL.res'.format(self.corpus, self.qtype)
        running_param = '-d '
        predictions_dir = self.predictions_dir + 'uef/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)

    def _generate_lists_uef(self):
        predictor_exe = 'python3.6 ~/repos/IRQPP/addWorkingsetdocs.py'
        parameters = '~/QppUqvProj/Results/{}/test/{}/QL.res'.format(self.corpus, self.qtype)
        running_param = '-d '
        predictions_dir = self.predictions_dir + 'uef/data/'
        queries = predictions_dir + 'queriesUEF'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param)
        predictor_exe = '~/SetupFiles-indri-5.6/runqueryql/IndriRunQueryQL'
        parameters = '~/QppUqvProj/Results/{}/test/indriRunQF.xml'.format(self.corpus)
        running_param = '-fbDocs='
        predictions_dir = self.predictions_dir + 'uef/lists/'
        self.__run_predictor(predictions_dir, predictor_exe, parameters, running_param, lists=True, queries=queries)

    def calc_aggregations(self, predictor):
        print('----- Calculating aggregated predictions results -----')
        script = 'python3.6 ~/repos/IRQPP/aggregateUQV.py'
        raw_dir = os.path.normpath('{}/{}/predictions'.format(self.predictions_dir, predictor))
        for n in NUM_DOCS:
            for func in AGGREGATE_FUNCTIONS:
                predictions_dir = self.predictions_dir.replace('raw', func)
                output = '{}{}/predictions/predictions-{}'.format(predictions_dir, predictor, n)
                ensure_dir(output)
                raw_res = '{}/predictions-{}'.format(raw_dir, n)
                ensure_files([script.split(' ')[1], raw_res])
                run('{} -p {} -f {} > {}'.format(script, raw_res, func, output), shell=True)

    def calc_singles(self, predictor):
        print('----- Calculating UQV single predictions results -----')
        script = 'python3.6 ~/repos/IRQPP/singleUQV.py'
        raw_dir = os.path.normpath('{}/{}/predictions'.format(self.predictions_dir, predictor))
        for n in NUM_DOCS:
            for func in SINGLE_FUNCTIONS:
                predictions_dir = self.predictions_dir.replace('raw', func)
                output = '{}{}/predictions/predictions-{}'.format(predictions_dir, predictor, n)
                ensure_dir(output)
                raw_res = '{}/predictions-{}'.format(raw_dir, n)
                ensure_files([script.split(' ')[1], raw_res])
                run('{} -p {} -f {} > {}'.format(script, raw_res, func, output), shell=True)


class CrossValidation:
    # TODO: Implement CV
    def __init__(self):
        pass

    def __run_predictor(self, predictions_dir, predictor_exe, parameters, running_param, lists=False):
        # ~/QppUqvProj/Results/ClueWeb12B/basicPredictions/uef/clarity $ python3.6 ~/repos/IRQPP/crossval.py -l ~/QppUqvProj/Results/ClueWeb12B/test/2_folds_30_repetitions.json --labeled ../../../test/basic/QLmap1000 -p predictions/
        #
        # Mean : 0.2692
        # Variance : 0.0019
        # Standard Deviation : 0.0435
        pass


class GenerateTable:
    def __init__(self):
        pass


def ensure_dir(file_path):
    # tilde expansion
    file_path = os.path.expanduser(file_path)
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def ensure_files(files):
    for file in files:
        _file = file.split(' ')
        for file in _file:
            # tilde expansion
            file_path = os.path.expanduser(file)
            assert os.path.isfile(file_path), "The file {} doesn't exist. Please create the file first".format(file)


def main(args):
    generate_functions = {'clarity': GeneratePredictions.generate_clartiy,
                          'nqc': GeneratePredictions.generate_nqc,
                          'wig': GeneratePredictions.generate_wig,
                          'qf': GeneratePredictions.generate_qf,
                          'uef': GeneratePredictions.generate_uef}

    calc_functions = {'single': GeneratePredictions.calc_singles,
                      'aggregated': GeneratePredictions.calc_aggregations}

    queries = args.queries
    corpus = args.corpus
    queries_type = args.qtype
    generate = args.generate
    predictor = args.predictor
    predictions_dir = '~/QppUqvProj/Results/{}/'.format(corpus)

    if queries_type == 'aggregated' or queries_type == 'single':
        predictions_dir = '{}/uqvPredictions/raw'.format(predictions_dir)
    else:
        predictions_dir = '{}/basicPredictions'.format(predictions_dir)

    predict = GeneratePredictions(queries, predictions_dir, corpus, queries_type)

    if generate:
        # Special case for generating results
        if predictor == 'all':
            for pred in PREDICTORS:
                generation_timer = Timer('{} generating'.format(pred))
                method = generate_functions.get(pred, None)
                assert method is not None, 'No applicable generate function found for {}'.format(pred)
                method(predict)
                generation_timer.stop()
            else:
                generation_timer = Timer('{} generating'.format(predictor))
                method = generate_functions.get(predictor, None)
                assert method is not None, 'No applicable generate function found for {}'.format(predictor)
                method(predict)
                generation_timer.stop()

    if predictor == 'all':
        if queries_type != 'basic':
            for pred in PREDICTORS:
                method = calc_functions.get(queries_type, None)
                assert method is not None, 'No applicable calculation function found for {}'.format(queries_type)
                method(predict, pred)
                method(predict, 'uef/{}'.format(pred))
    else:
        if queries_type != 'basic':
            method = calc_functions.get(queries_type, None)
            assert method is not None, 'No applicable calculation function found for {}'.format(queries_type)
            method(predict, predictor)
            method(predict, 'uef/{}'.format(predictor))


if __name__ == '__main__':
    overall_timer = Timer('Total running')
    args = parser.parse_args()
    main(args)
    overall_timer.stop()
