from lib.agents import storage as sa
from lib import tools as t
import json

def translate(string):
    # The return value here is an array
    # [translation_success_status,translation,flag,order]
    def work(entry):
        out = entry['eng']
        order = entry['order']
        flag = entry['flag'] if 'flag' in entry else ''
        return [True, t.fill_in(string, out, order), flag, order]
    n_string = t.normalise_input(string)
    g_dicts = [sa.get_dictionaries()]
    g_dicts_entries = [di[n_string] for di in g_dicts if n_string in di]
    if len(g_dicts_entries) > 0:
        return [work(entry) for entry in g_dicts_entries]
    else:
        return [[False,string,None,None]]

def save(entries):
    new_entries_dict = {}
    for entry in entries:
        keys = sorted(entry.keys())
        i = 0
        while i < len(entry):
            print('\nSaving...')
            print('DE: ' + keys[i])
            print('EN: ' + json.dumps(entry[keys[i]]['eng'])[1:-1])
            i += 1
        new_entries_dict.update(entry)

    d = sa.get_dictionary(sa.OWN_DICT_NAME)
    d.update(new_entries_dict)
    sa.save_dictionary(sa.OWN_DICT_NAME,d)

def save_word(inp,outp):
    n_inp = t.normalise_input(inp)
    print('save_word: %s ==> %s'%(inp,outp))
    entry = {n_inp: {'eng': outp.lower(),
                                     'flag': '',
                                     'order': []}}
    save(entry)

def process_line(line):

    def skip(line):
        return 'skip'

    def make_entry(call, inp, out):
        inp, out, order = t.make_replace(inp,out)
        return {call: {'eng': out,
                                     'flag':'',
                                     'order': order}}

    def direct(line):
        call = line.n_input
        inp = line.source
        out = line.output
        return make_entry(call, inp, out)


    def cat(line):
        if t.cat_test(line.output):
            cat_entry = cat_cat(line)
            mem_entry = cat_member(line)
            cat_entry.update(mem_entry)
            return cat_entry
        else:
            return direct(line)

    def cat_cat(line):
        call = line.n_input
        inp = t.get_cat(line.source)
        outp = t.get_cat(line.output)
        return make_entry(call, inp, outp)

    def cat_member(line):
        call = t.nest(line.source, t.get_cat_member, t.normalise_input)
        inp = t.get_cat_member(line.source)
        outp = t.get_cat_member(line.output)
        return make_entry(call, inp, outp)

    if line.t_method not in ['direct', 'cat']:
        raise NameError(line.t_method)

    entry = eval(line.t_method + '(line)')

    if entry == 'skip':
        print('skipping save')
        return None
    else:
        return entry
