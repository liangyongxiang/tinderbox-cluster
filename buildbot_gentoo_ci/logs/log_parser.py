# Copyright 2021 Gentoo Authors
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

def getDBSession(config):
    #FIXME: Read the user/pass from file
    engine = sa.create_engine(config['database'])
    Session = sa.orm.sessionmaker(bind = engine)
    return Session()

def getMultiprocessingPool(config):
    return Pool(processes = int(config['core']))

def addPatternToList(Session, pattern_list, uuid):
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
            patten_dict = {}
            patten_dict['id'] = project_pattern.id
            patten_dict['project_uuid'] = project_pattern.project_uuid
            patten_dict['search'] = project_pattern_search
            patten_dict['start'] = project_pattern.start
            patten_dict['end'] = project_pattern.end
            patten_dict['status'] = project_pattern.status
            patten_dict['type'] = project_pattern.type
            patten_dict['search_type'] = project_pattern.search_type
            pattern_list.append(patten_dict)
    return pattern_list

def get_log_search_pattern(Session, uuid, default_uuid):
    # get pattern from the projects
    # add that to log_search_pattern_list
    log_search_pattern_list = []
    log_search_pattern_list = addPatternToList(Session, log_search_pattern_list, uuid)
    log_search_pattern_list = addPatternToList(Session, log_search_pattern_list, default_uuid)
    return log_search_pattern_list

def search_buildlog(log_search_pattern_list, logfile_text_dict, tmp_index, max_text_lines):
    # get text line to search
    text_line = logfile_text_dict[tmp_index]
    summery_dict = {}
    # loop true the pattern list for match
    for search_pattern in log_search_pattern_list:
        search_hit = False
        # check if should ignore the line
        #FIXME take the ignore line pattern from db
        if text_line.startswith('>>> /'):
            pass
        #if else re.search('./\w+/'):
        #    pass
        else:
            # search for match
            if search_pattern['search_type'] == 'in':
                if search_pattern['search'] in text_line:
                    search_hit = True
            if search_pattern['search_type'] == 'startswith':
                if text_line.startswith(search_pattern['search']):
                    search_hit = True
            if search_pattern['search_type'] == 'endswith':
                if text_line.endswith(search_pattern['search']):
                    search_hit = True
            if search_pattern['search_type'] == 'search':
                if re.search(search_pattern['search'], text_line):
                    search_hit = True
        # add the line if the pattern match
        if search_hit:
            summery_dict[tmp_index] = {}
            summery_dict[tmp_index]['text'] = text_line
            summery_dict[tmp_index]['type'] = search_pattern['type']
            summery_dict[tmp_index]['status'] = search_pattern['status']
            summery_dict[tmp_index]['id'] = search_pattern['id']
            summery_dict[tmp_index]['search_pattern'] = search_pattern['search']
            # add upper text lines if requested
            # max 5
            if search_pattern['start'] != 0:
                i = tmp_index - search_pattern['start'] - 1
                match = True
                while match:
                    i = i + 1
                    if i < (tmp_index - 9) or i == tmp_index:
                        match = False
                    else:
                        if not i in summery_dict:
                            summery_dict[i] = {}
                            summery_dict[i]['text'] = logfile_text_dict[i]
                            summery_dict[i]['type'] = 'info'
                            summery_dict[i]['status'] = 'info'
                            summery_dict[i]['id'] = 0
                            summery_dict[i]['search_pattern'] = 'auto'
            # add lower text lines if requested
            # max 5
            if search_pattern['end'] != 0:
                i = tmp_index
                end = tmp_index + search_pattern['end']
                match = True
                while match:
                    i = i + 1
                    if i > max_text_lines or i > end:
                        match = False
                    else:
                        if not i in summery_dict:
                            summery_dict[i] = {}
                            summery_dict[i]['text'] = logfile_text_dict[i]
                            summery_dict[i]['type'] = 'info'
                            summery_dict[i]['status'] = 'info'
                            summery_dict[i]['id'] = 0
                            summery_dict[i]['search_pattern'] = 'auto'
        else:
            # we add all line that start with ' * ' as info
            # we add all line that start with '>>>' but not '>>> /' as info
            if text_line.startswith(' * ') or text_line.startswith('>>>'):
                if not tmp_index in summery_dict:
                    summery_dict[tmp_index] = {}
                    summery_dict[tmp_index]['text'] = text_line
                    summery_dict[tmp_index]['type'] = 'info'
                    summery_dict[tmp_index]['status'] = 'info'
                    summery_dict[tmp_index]['id'] = 0
                    summery_dict[tmp_index]['search_pattern'] = 'auto'
    if summery_dict == {}:
        return None
    return summery_dict

def getConfigSettings():
    configpath = os.getcwd().split('workers/')[0]
    with open(configpath + 'logparser.json') as f:
        config = json.load(f)
    return config

def runLogParser(args):
    index = 1
    max_text_lines = 0
    logfile_text_dict = {}
    config = getConfigSettings()
    Session = getDBSession(config)
    mp_pool = getMultiprocessingPool(config)
    #NOTE: The patten is from https://github.com/toralf/tinderbox/tree/master/data files.
    # Is stored in a db instead of files.
    log_search_pattern_list = get_log_search_pattern(Session, args.uuid, config['default_uuid'])
    Session.close()
    #FIXME: UnicodeDecodeError: 'utf-8' codec can't decode byte ... in some logs
    with io.TextIOWrapper(io.BufferedReader(gzip.open(args.file, 'rb'))) as f:
        for text_line in f:
            logfile_text_dict[index] = text_line.strip('\n')
            index = index + 1
            max_text_lines = index
        f.close()
    # run the parse patten on the line
    for tmp_index, text in logfile_text_dict.items():
        res = mp_pool.apply_async(search_buildlog, (log_search_pattern_list, logfile_text_dict, tmp_index, max_text_lines,))
        if res.get() is not None:
            print(json.dumps(res.get()))
    mp_pool.close()
    mp_pool.join()
