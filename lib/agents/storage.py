# -*- coding: utf-8 -*-
import getpass
import json
import os
import inspect

ROOT = os.getcwd()
HOME = os.path.expanduser('~')
TCF = os.path.join(ROOT, 'data')
USERNAME = getpass.getuser()
CONF_PATH = 'data/tc_config.json'
COOKIE_PATH = 'data/cookies.json'


if os.path.exists(CONF_PATH):
    with open(CONF_PATH) as data:
        CONF = json.load(data)
        CONF['browser'] = 'c' if USERNAME == 'samuelob' else 'f'
        CONF['db_path'] = CONF['db_path'].replace('{USERNAME}', USERNAME)
    if len(CONF) > 0:
        DBF = CONF['db_path']
        OWN_DICT_NAME = CONF['shortname'] + '_dict.json'
        OWN_DICT_PATH = os.path.join(TCF, CONF['shortname'] + '_dict.json')
        BASE_DICT_NAME = 'base_dict.json'
        INPUT_FILE_PATH = os.path.join(TCF, 'input.txt')
        OUTPUT_FILE_PATH = os.path.join(TCF, 'output.txt')
    else:
        print("Critical: Please check your tc_config file. If the problem persists, contact me")

        # if 'db_path' in CONF:
        # else:
        #   DBF = 'data'


def get_config():
    with open(CONF_PATH) as data:
        CONF = json.load(data)
    return CONF


def config_present_check():
    if not os.path.exists(CONF_PATH):
        return False
    else:
        return True


def dpj(filename):
    return os.path.join(DBF, filename)


def load_worker_files():
    return load_tmp(OUTPUT_FILE_PATH), load_tmp(INPUT_FILE_PATH)


def save_worker_files(article):
    inp = article.art_str(field="source")
    save_tmp(INPUT_FILE_PATH, inp)
    outp = article.art_str(field="output")
    outp = article.final_checks(outp, True)
    save_tmp(OUTPUT_FILE_PATH, outp)


def load_tmp(filename):
    path = dpj(filename)
    with open(path, 'r') as input:
        return [line for line in input.read().splitlines()]


def save_tmp(filename, str_value):
    if not os.path.exists(TCF):
        os.makedirs(TCF)
    with open(filename, 'w') as output:
        output.write(str_value)


def jsonLoad(fileName):
    with open(fileName) as data:
        return json.load(data)


def jsonSave(fileName, inp_dict):
    with open(fileName, 'w') as outfile:
        json.dump(inp_dict, outfile, indent=3)


def get_conf():
    return jsonLoad(CONF_PATH)


def save_conf(conf):
    jsonSave(CONF_PATH, conf)


def get_cookies():
    return jsonLoad(COOKIE_PATH)


def save_cookies(cookies):
    jsonSave(CONF_PATH, cookies)


def get_dictionary(filename):
    return jsonLoad(dpj(filename))


def save_dictionary(filename, t_dict):
    jsonSave(dpj(filename), t_dict)


def get_dictionaries():
    return jsonLoad(dpj(OWN_DICT_NAME))
