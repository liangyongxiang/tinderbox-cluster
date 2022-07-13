# Copyright 2022 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

import sys
from multiprocessing import Pool, cpu_count
import re
import io
import gzip
import json
import os
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa
import argparse

Base = declarative_base()

class ProjectsPattern(Base):
    __tablename__ = "projects_pattern"
    id = sa.Column(sa.Integer, primary_key=True)
    project_uuid = sa.Column(sa.String(36), nullable=False)
    search = sa.Column(sa.String(50), nullable=False)
    start = sa.Column(sa.Integer, default=0)
    end = sa.Column(sa.Integer, default=0)
    status = sa.Column(sa.Enum('info', 'warning', 'ignore', 'error'), default='info')
    type = sa.Column(sa.Enum('info', 'qa', 'compile', 'configure', 'install', 'postinst', 'prepare', 'pretend', 'setup', 'test', 'unpack', 'ignore', 'issues', 'misc', 'elog'), default='info')
    search_type = sa.Column(sa.Enum('in', 'startswith', 'endswith', 'search'), default='in')

def get_pattern_dict(project_pattern):
    patten_dict = {}
    patten_dict['id'] = project_pattern.id
    patten_dict['project_uuid'] = project_pattern.project_uuid
    patten_dict['search'] = project_pattern.search
    patten_dict['status'] = project_pattern.status
    patten_dict['type'] = project_pattern.type
    return patten_dict

def addPatternToList(Session, log_search_pattern, uuid):
    for project_pattern in Session.query(ProjectsPattern).filter_by(project_uuid=uuid).all():
        # check if the search pattern is vaild
        project_pattern_search = project_pattern.search
        try:
            re.compile(project_pattern_search)
        except re.error:
            print("Non valid regex pattern")
            print(project_pattern.search)
            print(project_pattern.id)
        else:
            if project_pattern.type == 'ignore':
                log_search_pattern['ignore'].append(get_pattern_dict(project_pattern))
            if project_pattern.type == 'test':
                log_search_pattern['test'].append(get_pattern_dict(project_pattern))
            else:
                log_search_pattern['default'].append(get_pattern_dict(project_pattern))
    return log_search_pattern

def get_log_search_pattern(Session, uuid, default_uuid):
    # get pattern from the projects and add that to log_search_pattern
    log_search_pattern = {}
    log_search_pattern['ignore'] = []
    log_search_pattern['default'] = []
    log_search_pattern['test'] = []
    log_search_pattern = addPatternToList(Session, log_search_pattern, uuid)
    log_search_pattern = addPatternToList(Session, log_search_pattern, default_uuid)
    return log_search_pattern

def get_search_pattern_match(log_search_pattern, text_line):
    for search_pattern in log_search_pattern:
        if re.search(search_pattern['search'], text_line):
            return search_pattern
    return False

def search_buildlog(log_search_pattern, text_line, index):
    summary = {}
    #FIXME: add check for test
    # don't log ignore lines
    if get_search_pattern_match(log_search_pattern['ignore'], text_line):
        return False
    # search default pattern
    search_pattern_match = get_search_pattern_match(log_search_pattern['default'], text_line)
    if search_pattern_match:
        summary[index] = dict(
            text = text_line,
            type = search_pattern_match['type'],
            status = search_pattern_match['status'],
            id = search_pattern_match['id'],
            search_pattern = search_pattern_match['search']
            )
        return summary
    # we add all line that start with ' * ' or '>>>' as info
    if text_line.startswith(' * ') or text_line.startswith('>>>'):
        summary[index] = dict(
            text = text_line,
            type = 'info',
            status = 'info',
            id = 0,
            search_pattern = 'auto'
            )
        return summary
    return False

def getConfigSettings():
    #configpath = os.getcwd()
    with open('logparser.json') as f:
        config = json.load(f)
    return config

def getDBSession(config):
    engine = sa.create_engine(config['database'])
    Session = sa.orm.sessionmaker(bind = engine)
    return Session()

def getMultiprocessingPool(config):
    return Pool(processes = int(config['core']))

def getJsonResult(results):
    for r in results:
        try:
            value = r.get()
        except Exception as e:
            print(f'Failed with: {e}')
        else:
            if value:
                print(json.dumps(value), flush=True)

def runLogParser(args):
    index = 1
    logfile_text_dict = {}
    config = getConfigSettings()
    Session = getDBSession(config)
    #mp_pool = getMultiprocessingPool(config)
    summary = {}
    #NOTE: The patten is from https://github.com/toralf/tinderbox/tree/master/data files.
    # Is stored in a db instead of files.
    log_search_pattern = get_log_search_pattern(Session, args.uuid, config['default_uuid'])
    Session.close()
    # read the log file to dict
    for text_line in io.TextIOWrapper(io.BufferedReader(gzip.open(args.file)), encoding='utf8', errors='ignore'):
        logfile_text_dict[index] = text_line.strip('\n')
        index = index + 1
    # run the search parse pattern on the text lines
    #params = [(log_search_pattern, text, line_index,) for line_index, text in logfile_text_dict.items()]
    with getMultiprocessingPool(config) as pool:
        results = list(pool.apply_async(search_buildlog, args=(log_search_pattern, text, line_index,)) for line_index, text in logfile_text_dict.items())
        #results = pool.starmap(search_buildlog, params)
        getJsonResult(results)
        pool.close()
        pool.join()

def main():
# get filename, project_uuid default_project_uuid
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True)
    parser.add_argument("-u", "--uuid", required=True)
    args = parser.parse_args()
    runLogParser(args)
    sys.exit()

if __name__ == "__main__":
    main()
