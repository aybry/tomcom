# -*- coding: utf-8 -*-
import re
import json
import os
from lib.agents import storage as stag
from pyquery import PyQuery as pq
import platform
if platform.system() == "Darwin":
    from Carbon import AppleEvents
    from Carbon import AE
elif platform.system() == "Windows":
    from pywinauto.application import Application


#=============================Procedural Functions=============================
def direct_test(str):
    g_dicts,b_dict = stag.get_dictionaries()
    dicts = g_dicts.append(b_dict)
    return any(map(lambda di: str in di,dicts))

def cat_test(str):
    return (str.count(':') == 1 and
                    str.strip()[-1] != ':')

def dim_test(str):#dimensions test
    dim_regex = get_dimension_regex()
    return bool(dim_regex.search(str))

def digit_test(str):#digit test
    return bool(re.search(r"\d",str))

def inter_str(str,fill,rep='|>num<|'):
    beg = str.index(rep)
    end = beg+len(rep)
    return str[:beg]+fill+str[end:]

def normalise_input(string, remove_single_characters=False):
    # try:
    #     string = string.encode('iso-8859-1')
    # except UnicodeDecodeError:
    #     pass
    # print('before:', string, type(string))
    cleaner_regex = get_cleaner_regex()
    dim_regex = get_dimension_regex()
    num_regex = get_number_regex()
    tmp = string.lower().strip()
    tmp = decimal_replace(tmp)
    # print(cleaner_regex.sub(' ', tmp))
    # print(cleaner_regex.sub(' ', tmp.decode('utf-8').encode('iso-8859-1')))
    tmp = cleaner_regex.sub(' ', tmp)
    tmp = num_regex.sub('|>num<|',tmp)
    tmp = dim_regex.sub('|>dim<|',tmp)
    tmp = space_replace(tmp)
    if remove_single_characters:
        tmp = tmp.split()
        tmp = [word for word in tmp if len(word)>1]
        tmp = ' '.join(tmp)
    # print('after:', tmp.strip())
    # print('')
    return tmp.strip()

def get_numbers(str):
    num_regex = get_number_regex()
    return num_regex.findall(str)

def get_cat(str):
    assert cat_test(str), "tools.get_cat received a faulty string: %s"%str
    return str.split(':')[0].strip()

def get_cat_member(str):
    assert cat_test(str), "tools.get_cat_member received a faulty string: %s"%str
    return str.split(':')[1].strip()

def restore_upper(inp,outp):
    def char_num_mix_test(str):
        return bool(re.search(r"\d",str)) and bool(re.search(r"[a-zA-Z]",str))
    upper_words = [word for word in inp.split(' ') if sum([1 for c in word if c.isupper()]) > 1 or char_num_mix_test(word)]
    lv_upper_words = [word.lower() for word in upper_words]
    out_words = outp.split(' ')
    lv_out_words = [word.lower() for word in out_words]
    if len(upper_words) > 0:
        res_out = [out_words[idx] if word not in lv_upper_words else upper_words[lv_upper_words.index(word)] for idx,word in enumerate(lv_out_words)]
        # print(res_out)
        outp = ' '.join(res_out)
    return outp

def fill_in(source,target,order=[]):
    nums = get_number_regex().findall(decimal_replace(source))
    if order == []: order = range(len(nums))
    dims = [fds(s) for s in get_dimension_regex().findall(source)]
    if len(nums) == target.count('|>num<|'):
        try:
            assert len(nums) == len(order)
        except AssertionError:
            print('source: ' + source)
            print('target: ' + target)
            print('nums: ' + str(len(nums)) + '\torder: ' + str(len(order)))
            input('\nCheck these strings in dict and restart tomcom!')
            raise AssertionError
        for idx in order:
            target = inter_str(target,nums[idx])
    else:
        print('There are %s numbers in this line: \n\n%s\n\nbut %s |>num<| marks in this output: \n\n%s'%(len(nums),source,target.count('|>num<|'),target))
    if len(dims) == target.count('|>dim<|'):
        for dim in dims:
            target = inter_str(target,dim,'|>dim<|')
    else:
        print('There are %s dimension strings in this line \n\n%s\n\nbut %s |>dim<| marks this output \n\n%s'%(len(dims),source,target.count('|>dim<|'),target))
    return decimal_replace(target)

def make_replace(inp,outp):
    i_nums = nest(inp,decimal_replace,get_numbers)
    o_nums = nest(outp,decimal_replace,get_numbers)
    if all([x in o_nums for x in i_nums]):
        res_i = nest(inp,decimal_replace,number_replace,dim_replace).strip()
        res_o = nest(outp,decimal_replace,number_replace,dim_replace).strip()
        order = target_order(i_nums,o_nums)
    else:
        res_i = nest(inp,decimal_replace,dim_replace).strip()
        res_o = nest(outp,decimal_replace,dim_replace).strip()
        order = []
    res_o = thousands_replace(res_o)
    res_o = restore_upper(res_i,res_o)
    return (res_i,res_o,order)

def target_order(lst1, lst2):
    res = []
    for element in lst1:
        idx = lst2.index(element)
        res.append(idx)
        lst2[idx]=None
    return res

def parse_url(url, array=False):
    # the array parameter switches:
        # True => returns a string array with the text of each line from the article
        # False => returns an array with Line objects for each line of the article
    page = pq(url=url, encoding='utf-8', headers={'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:83.0) Gecko/20100101 Firefox/83.0'})
    if len(page('.rs-prod-text')) > 0:
        page = page('.rs-prod-text').children()
    elif len(page('.rs-prod-ltext')) > 0:
        page = page('.rs-prod-ltext').children()
    else:
        page = page('.tr-prod-ltext').children()
    line_dict_ary = []
    p_ind = 0
    for node in page:
        # print(node.tag)
        if node.tag == 'h2':
            inp = str(pq(node).text())
            d = {'type': 'title', 'html-class': 'h2', 'line': inp, 'prefix': '@!'}
            line_dict_ary.append(d)
        elif node.tag == 'ul':
            for li in node.findall("li"):
                if len(li) > 0:
                    a_nodes = li[0].findall("a")
                inp = str(pq(li).text())
                if len(a_nodes) > 0:
                    a_text = [url.text for url in a_nodes]
                    for url in a_text:
                        inp = inp.replace(url,"#" + url + "#")
                d = {'type':'bullet','html-class':'li','line':inp,'prefix':'@@'}
                line_dict_ary.append(d)
        elif node.tag == 'p':
            # if pq(node)('b').length > 0:
            #   text = pq(node).text()
            #   print(text)
            #   bold = pq(node)('b').text()
            #   bold_mu = '*'+pq(node)('b').text()+'*'
            #   inp = text.replace(bold,bold_mu)
            # else:
            #   try:
            #     inp = node.text
            #   except IndexError:
            inp = str(pq(node).text())
            d = {'type':'sub-title','html-class':'p','line':inp,'prefix':'@+','suffix':'@+@+'}
            line_dict_ary.append(d)
        else:
            d = {'type':'unknown','html-class':node.tag,'line':'Unknown line in product'}
            line_dict_ary.append(d)
    if array:
        return [line['line'] for line in line_dict_ary]
    else:
        return line_dict_ary

def parse_unformatted(text):
    lines_comma = text.split(',')
    lines_semicolon = text.split(';')
    if len(lines_comma) > len(lines_semicolon):
        lines = lines_comma
    else:
        lines = lines_semicolon
    line_dict_ary = []
    for idx, line in enumerate(lines):
        try:
            if line[0] == ' ':
                line = line[1:]
        except IndexError:
            continue
        if idx == 0:
            d = {'type': 'title',
                 'html-class': 'h2',
                 'line': line,
                 'prefix': '@!',
                 'src_was_formatted': False}
        else:
            d = {'type': 'bullet',
                 'html-class': 'li',
                 'line': line,
                 'prefix': '@@',
                 'src_was_formatted': False}
        line_dict_ary.append(d)
    return line_dict_ary

def init_tomcom():
    def y_n():
        print("Please enter 'y' for yes or 'n' for no")
        inp = input("Input: ")
        if inp not in ['y','n']:
            return y_n()
        else:
            return inp == 'y'
    def get_shortname():
        print("Please enter a shortname for your personal dictionary.\nYou should use the one from before, to continue using your dictionary.\nAlso, to continue using your old dictionary,\nplease copy the file into the tomcom directory.\nIf you do so, before entering the name, tomcom will immediately check to see if it's there.")
        return input("\nYour short_name: ")
    def get_login():
        print("\nTo login automatically, your thomann email and password will be required.")
        print("Your password will only be stored on your computer and used to automatically log you in.")
        # print("Do you want to use autologin?\n")
        # if y_n():
        #   print("\nGreat, please enter the email you used to sign in on the thomann website.")
        email = input("Email: ")
        pw = input("Password: ")
        print('If you made a mistake, you can edit it manually inside of tomcom/data/tc_config')
        return {'email':email,'password':pw}
    def get_db_path():
        print("\nTomcom needs the path to your dropbox to access the shared dictionaries. Please provide the path to take advantage of other peoples work ;-)")
        return input("\nDropbox shared_dictionaries path: ")
    def get_sublime():
        print("\nDo you want to work in a text editor?")
        print("(Default is working directly in the browser)")
        return y_n()
    def get_two_window_mode():
        print("\nIf you want you can use two browser windows side by side,\none for editing, one for the original article.")
        print("Do you want to use two windows?")
        return y_n()



    # def check_personal_dict():


# Preparation
    conf_path = stag.CONF_PATH
    cookie_path = stag.COOKIE_PATH
    # if not os.path.exists(conf_path): stag.jsonSave(conf_path,{})
    # if not os.path.exists(cookie_path): stag.jsonSave(cookie_path,[])




    # if setup == 's':
    #   print('\nYou need to provide the necessary information. Your information will remain on your computer only.')
    #   print('start setup process')
    #   conf = {}
    #   req_fields = ['shortname','login', 'db_path']
    #   get_info = [key for key in req_fields if key not in conf or len(str(conf[key]))==0]
    #   print('missing fields',get_info)
    #   for key in get_info:
    #     conf[key] = eval('get_'+key)()
    #   print(conf)
    #   should_run = False
    #   return should_run
    # elif setup == 'c':
    #   print('\nPlease copy the tc_config.json file into the tomcom/data directory and restart tomcom')
    #   should_run = False
    #   return should_run
    # elif conf:
    #   print('Config found')
    #   should_run = False
    #   return should_run
    # else:
    #   print('Wrong input. Shutting down. Restart to try again')
    #   should_run = False
    #   return should_run

    # # if not conf['sublime'] and 'two_window_mode' not in conf:
    # #   conf['two_window_mode'] = get_two_window_mode()
    # conf['browser'] == 'c'
    # stag.jsonSave(conf_path,conf)
    # own_dict_path = stag.OWN_DICT_NAME
    # if not os.path.exists(own_dict_path): stag.jsonSave(own_dict_path,{})
    # return conf

def get_config():
    print('\nHello there\ntc_config.json is missing.\nPlease copy your old tc_config.json file into: tomcom/data\nTomcom will check if it can find it where it needs it.')
    input("\nPlease hit enter after you copied the file.")
    while not os.path.exists(stag.CONF_PATH):
        print
        print('Something went wrong.\nPlease copy the file into the data folder of the directory you started tomcom from.\nIf the problem persist, you will need to get in touch with me.')
        print
        input("Please hit enter after you copied the file.")
    return stag.get_config()

def win_show(title_element):
    cb = lambda x,y: y.append(x)
    wins = []
    win32gui.EnumWindows(cb,wins)
    tgtWin = -1
    for win in wins:
        txt = win32gui.GetWindowText(win)
        if title_element in txt:
            time.sleep(1)
            win32gui.SystemParametersInfo(win32con.SPI_SETFOREGROUNDLOCKTIMEOUT, 0, win32con.SPIF_SENDWININICHANGE | win32con.SPIF_UPDATEINIFILE)
            win32gui.SetForegroundWindow(win)
            break

def mac_show(bundle_id):
    target = AE.AECreateDesc(AppleEvents.typeApplicationBundleID, bundle_id)
    activateEvent  = AE.AECreateAppleEvent( 'misc', 'actv', target, AppleEvents.kAutoGenerateReturnID, AppleEvents.kAnyTransactionID)
    activateEvent.AESend(AppleEvents.kAEWaitReply, AppleEvents.kAENormalPriority, AppleEvents.kAEDefaultTimeout)


#=====================================Regex=====================================
def get_cleaner_regex():
    return re.compile(u'[^A-Za-zäöüß 0-9.°+-/-±"%&()Øø><²]\'', re.UNICODE)

def get_dimension_regex():
    return re.compile(r"\(?[lbthdwDWLBTH] *x *[ldwbthLDWBTH] *x *[lbdwthLDWBTH]\)?")

def get_number_regex():
    return re.compile(r"\d+\.\d+|\d+")

def format_article_nr(sr):
    sr=re.compile(r"(\d{3}) *?(\d{3})").sub(r"\1\2",sr)
    return (re.compile(r"(art|type)\.? *?# *?(\d{6}) *?#",re.I).sub(r"Article Nr #\2#",sr) )

def remove_space_between_digit_and_inch_sign(sr):
    return re.compile(r'(\d) "').sub(r'\1"',sr)

def capitalize_first_letter(sr):
    return ( re.compile(r"^.*?([a-zA-Z]{1})")
                         .sub(lambda pat: pat.group(0).upper(),sr) )

def upper_case_after_colon(sr):
    return ( re.compile(r":\s*?([a-zA-Z]{1})")
                         .sub(lambda pat: pat.group(0).upper(),sr) )


#=====================================Tools=====================================
def cap_first(sr):
    if len(sr) > 1:
        return sr[0].capitalize()+sr[1:]
    else:
        return sr

def cap_word_after_nums(sr):
    nreg = get_number_regex()
    words = sr.split(' ')
    if len(words) > 1 and len(nreg.sub('',words[0].strip())) == 0:
        if words[1] not in ['mm']:
            words[1] = cap_first(words[1])
        return ' '.join(words)
    else:
        return sr


def space_replace(str):
    return re.sub(r" +",r" ",str)

def number_replace(str):
    num_regex = get_number_regex()
    return num_regex.sub('|>num<|',str)

def dim_replace(str):
    if dim_test(str):
        dim_regex = get_dimension_regex()
        dim_ary = dim_regex.findall(str)
        if len(dim_ary) == 1:
            return dim_regex.sub('|>dim<|',str)
        elif len(dim_ary) > 1:
            print('dim_replace encountered multiple dimensions: %s\n Dimensions not replaced!!'%str)
            return str
    else:
        return str

def rd(str):#remove_dimensions
    regex = get_dimension_regex()
    return regex.sub('',str)

def gd(str):#get_dimensions
    regex = get_dimension_regex()
    return regex.search(str).group()

def fd(dim,spaces=True):#format_dimensions
    spacer = ' x ' if spaces else 'x'
    val = re.sub(r" +|\(|\)",r"",dim).upper()
    val = val.replace('X',spacer)
    return '(%s)'%val

def fds(str,spacer=True):#format_dimensions_string
    if dim_test(str):
        dim = gd(str)
        translation = td(fd(dim,spacer))
        return str.replace(dim,translation)
    else:
        return str

def td(dim):#translate_dimensions
    repl_pattern=[('T','D'),('B','W'),('(',''),(')','')]
    for k,v in repl_pattern:
        dim = dim.replace(k,v)
    return '(%s)'%dim

def sd(str,spacer=True):#sd
    dims = gd(str)
    rep = fd(dims,spacer)
    return str.replace(dims,rep)

def decimal_replace(str):
    return re.sub(r"(\d+),(\d+)",r"\1.\2",str)

def thousands_replace(str):
    return re.sub(r"(\d{1,3})\.(\d{3})",r"\1,\2",str)

# def insert_into_string(inp,str,index):
#   return str[:index]+inp+str[index:]

def jstr(dict):
    return json.dumps(dict, sort_keys=True, indent=3, separators=(',', ': '))

def l2d(line):
    # for key,val in sub.iteritems():
    #   sub[key] = l2d(val)
    return {'source':line.source,
    'n_input':line.n_input,
    'prefix':line.prefix,
    'suffix':line.suffix,
    'output':line.output,
    't_method':line.t_method,
    'ok':line.ok,
    'save':line.save}

def flatten(kram):
    res=[]
    for it in kram:
        if isinstance(it,list):
            res+=it
        else:
            res.append(it)
    return res

#===============================Higher Functions===============================
def nest(arg,*list):
    for f in list:
        arg = f(arg)
    return arg