# -*- coding: utf-8 -*-
from lib.agents import storage as stag
from lib import tools as t
from lib.agents import dictionary as diag

import json
import urllib
import requests
import re
import time
import os
import platform
import html

from bs4 import BeautifulSoup
from html.parser import HTMLParser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as c_options
from selenium.webdriver.firefox.options import Options as f_options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from datetime import date
from google.cloud import translate


class Browser(object):
    def __init__(self, conf, manual_url=None):
        self.conf = conf
        self.url = ''
        self.manual_url = manual_url
        config = stag.get_config()

        if conf['browser'] == 'f':
            options = f_options()
            options.add_argument("-profile")
            options.add_argument(config['firefox_profile'])
            self.driver = webdriver.Firefox(
                firefox_options=options,
                service_args=["--marionette-port", "2828"],
            )
        else:
            options = c_options()

            if 'chrome_profile' in config:
                options.add_argument("user-data-dir="+config['chrome_profile']) #Path to your chrome profile
                options.add_argument("disable-infobars")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)

                self.driver = webdriver.Chrome(chrome_options=options)
            else:
                self.driver = webdriver.Chrome()
        self.open('https://language:awesumpassword123@language.thomann.de')
        if len(self.get_cookies())>0:#if cookies are younger then 45 mins and one is present
            print('Cookie found, trying to use it. Please wait.')
            self.set_cookies()
            self.open()
            try:
                WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.LINK_TEXT, "Orig. Page")))
            except:
                self.login()
        else:
            self.login()

    def login(self):
        try:
            l1 = self.driver.find_element_by_id("l_number")
            l2 = self.driver.find_element_by_id("l_pass")
            l3 = self.driver.find_element_by_id("l_login")
            l1.send_keys(self.conf['login']['email'])
            l2.send_keys(self.conf['login']['password'])
            l3.send_keys(Keys.ENTER)
            print('Logging in, please wait...')
        except:
            pass
        try:
            WebDriverWait(self.driver, 300).until(EC.presence_of_element_located((By.LINK_TEXT, "Orig. Page")))
        except:
            print('Login failed. Please check the internet connection and try again.')
        finally:
            if len(self.driver.get_cookies()) > 0:
                self.save_cookies()

    def logged_in(self, retried_once=False):
        self.open()
        try:
            self.driver.find_element_by_link_text("Orig. Page")
            return True
        except NoSuchElementException:
            if not retried_once:
                self.driver.refresh()
                self.logged_in(True)
            else:
                print("It seems like you are not logged in.")
            return False

    def save_cookies(self):
        stag.jsonSave('data/cookies.json',self.driver.get_cookies())

    def get_cookies(self):
        return stag.jsonLoad('data/cookies.json')

    def set_cookies(self):
        self.driver.delete_all_cookies()
        cks = stag.jsonLoad('data/cookies.json')
        self.driver.add_cookie(cks[-1])

    def open(self,url='https://language.thomann.de'):
        self.driver.get(url)

    def quit(self):
        self.save_cookies()
        self.driver.quit()

    def logout(self):
        stag.jsonSave('data/cookies.json', [])
        self.driver.get("https://language.thomann.de?controller=login&action=logout")
        self.driver.quit()

    def get_text(self):
        text_area = self.driver.find_element_by_id("ltext")
        return text_area.get_attribute('value')

    def paste_translation(self, translation):
        text_area = self.driver.find_element_by_id("ltext")
        text_area.send_keys(Keys.RETURN)
        self.driver.execute_script(
            f'$("#ltext").val($("#ltext").val() + decodeURIComponent("{urllib.parse.quote(translation)}")).keyup();')

    def del_prev_translation(self):
        # self.driver.refresh()
        text_area = self.driver.find_element_by_id("ltext")
        prev_trsln = text_area.get_attribute('value')
        top_line = prev_trsln.split('\n')[0]

        for key in TOPLINE_REPLACEMENT_DICT:
            if key in top_line:
                val = TOPLINE_REPLACEMENT_DICT[key]
                top_line = top_line.replace(key, val)
                print(f'\nReplaced {key} in top line with {val}')

        if top_line == '':
            top_line = self.driver.find_element_by_id('artname').text
            print(f'Top line was empty, using {top_line}.')

        text_area.clear()
        self.driver.execute_script(
            f'$("#ltext").val(decodeURIComponent("{urllib.parse.quote(top_line)}")).change();')

    def submit_translation(self):
        if self.conf['browser'] == 'f':
            submit_button = self.driver.find_elements_by_class_name("fake-button")[0]
            submit_button.click()
        elif self.conf['browser'] == 'c':
            self.driver.execute_script(
                'document.getElementsByClassName("fake-button")[0].click();'
            )

    def get_article_url(self):
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.LINK_TEXT, "Orig. Page")))
        try:
            a_link = self.driver.find_element_by_link_text("Orig. Page")
            return a_link.get_attribute("href")
        except (StaleElementReferenceException, NoSuchElementException):
            time.sleep(0.5)
            self.get_article_url()

    def get_article_no(self):
        return self.driver.find_element_by_id("my_artnr").text

    def skip_article(self):
        btn = self.driver.find_element_by_link_text('Skip')
        btn.send_keys(Keys.ENTER)

    def remember_article_url(self):
        self.url = self.get_article_url()
        if self.manual_url is not None:
            return self.manual_url
        else:
            return self.url

    def refresh(self):
        self.driver.refresh()

    def show(self):
        if platform.system() == "Darwin":
            if self.conf['browser'] == 'f':
                bundle = "org.mozilla.FireFox"
            elif self.conf['browser'] == 'c':
                bundle = "com.google.Chrome"
            t.mac_show(bundle)
        elif platform.system() == "Windows":
            # chrome = Application().connect(title_re="Thomann Language Tool",class_name="Chrome_WidgetWin_1")
            # chrome.windows_()[0].SetFocus()
            t.win_show('Thomann Language')

class Article(object):
    def __init__(self, url):
        self.url = url
        self.src_was_formatted = True
        self.l_obj_ary = [Line(line_dict) for line_dict in t.parse_url(url) if line_dict['line'] != '']
        line_count = len(self.l_obj_ary)
        self.finished = False
        if line_count == 1:
            self.src_was_formatted = False
            self.l_obj_ary = [Line(line_dict, False) for line_dict in t.parse_unformatted(self.l_obj_ary[0].source)]
        self.load_rules()
        print('\nProcessing: ' + url[26:])

    def art_str(self, prefix=False, field="source"):
        return '\n'.join(self.line_ary(prefix, field))

    def final_checks(self, res, pre_translate=False):
        for repl in FINAL_REPLACEMENT_DICT.keys():
            if repl in res:
                res = res.replace(repl, FINAL_REPLACEMENT_DICT[repl])
                print(
                    f'\nReplaced \'{repl}\' with \'{FINAL_REPLACEMENT_DICT[repl]}\'')

        for word in CAREFUL_LIST:
            if word in res:
                print(
                    f'Warning! Found \'{word}\' in translation. Is that really what you meant?')

        for f_c in FALSE_COLLOCATION_DICT:
            if f_c in res and FALSE_COLLOCATION_DICT[f_c] in res:
                print('\n' + ('*' * 40))
                print(
                    f'Warning! Found \'{f_c}\' and \'{FALSE_COLLOCATION_DICT[f_c]}\' in translation.')
                print('\n' + ('*' * 40))
                print(f'Press enter when ready...')

        return res

    def alternative_rows(self):
        if any([len(line.alt)>0 for line in self.l_obj_ary]):
            appendix = '\n\n'+'Alternative Translations'.center(60,'=')+'\n\n'
            for idx,line in enumerate(self.l_obj_ary):
                if len(line.alt) > 0:
                    appendix+='Row: %s \n'%(idx+1)
                    for idx,row in enumerate(line.alt):
                        appendix+='%s: %s\n'%((idx+1),row.decode('utf-8'))
            return appendix
        else:
            return ''

    def line_ary(self, prefix=False, field="source"):
        if prefix:
            try:
                return [line.prefix + getattr(line, field) + line.suffix for line in self.l_obj_ary]
            except AttributeError:
                return [line['prefix'] + line['output'] + line['suffix'] for line in self.l_obj_ary]

        else:
            if field == 'source':
                return [getattr(line, field) for line in self.l_obj_ary]
            else:
                return ['\t'.join([getattr(line, field)] + line.commands) for line in self.l_obj_ary]

    def ready(self):
        try:
            ret_val = all([line.ok for line in self.l_obj_ary])
            return ret_val
        except AttributeError: # no 'ok' is set if src article was not formatted
            if self.src_was_formatted and self.finished:
                return True
            else:
                return False

    def load_rules(self):
        man_rules = stag.jsonLoad('data/manual_rules.json')
        global UPPER_CASE_WORDS
        global NON_CAP_TITLE_WORDS
        global GOOGLE_API_REPLACEMENT_DICT
        global FINAL_REPLACEMENT_DICT
        global CAREFUL_LIST
        global FALSE_COLLOCATION_DICT
        global TOPLINE_REPLACEMENT_DICT
        UPPER_CASE_WORDS = man_rules['UPPER_CASE_WORDS']
        NON_CAP_TITLE_WORDS = man_rules['NON_CAP_TITLE_WORDS']
        GOOGLE_API_REPLACEMENT_DICT = man_rules['GOOGLE_API_REPLACEMENT_DICT']
        FINAL_REPLACEMENT_DICT = man_rules['FINAL_REPLACEMENT_DICT']
        CAREFUL_LIST = man_rules['CAREFUL_LIST']
        FALSE_COLLOCATION_DICT = man_rules['FALSE_COLLOCATION_DICT']
        TOPLINE_REPLACEMENT_DICT = man_rules['TOPLINE_REPLACEMENT_DICT']


class Line(object):
    def __init__(self, inp_dic, src_was_formatted=True):
        if type(inp_dic) == type(u''):  # apparently this is just here, in case the Line object is called from somehwere else then the parse function
            inp_dic = {'line': inp_dic}
        assert type(str(inp_dic['line'])) == type(u'')
        self.source = str(inp_dic['line'])
        self.n_input = t.normalise_input(self.source)
        self.type = inp_dic['type']
        self.prefix = inp_dic.get('prefix', '')
        self.suffix = inp_dic.get('suffix', '')
        self.output = t.decimal_replace(self.source)  # per default, the line will need to be translated. So we put what's to be translated here.
        self.commands = []
        self.alt = []
        self.t_method = None
        self.ok = False
        self.save = False
        self.src_was_formatted = src_was_formatted

        # starting analysis and preparation of line.
        if t.cat_test(self.source):
            self.n_input = t.nest(self.source, t.get_cat, t.normalise_input)
            self.t_method = 'cat'
        else:
            self.t_method = 'direct'


class Lator(object):
    def __init__(self, lines):
        self.lines = lines
        self.cmd_dict = {'cat':    self.cat_translation,
                         'direct': self.direct_translation}
        self.trans_w_google = []

    def run(self):
        for l_idx, line in enumerate(self.lines):
            assert line.t_method in self.cmd_dict, "Unknown translation method: %s for line: %s"%(line.t_method.split('+')[0], line.source)
            self.cmd_dict[line.t_method](line, l_idx)     # start translation

        texts_for_google = []
        for line_tpl in self.trans_w_google:
            try:
                texts_for_google.append(line_tpl[1].source)
            except AttributeError:
                assert line_tpl[2] in ['cat', 'member']
                texts_for_google.append(line_tpl[1])

        if len(texts_for_google) != 0:
            g_trans_texts = self.google_translate(texts_for_google)
            for google_input_tuple, text in zip(self.trans_w_google, g_trans_texts):
                l_idx = google_input_tuple[0]

                try:
                    cat_mem = google_input_tuple[2]
                    # If here, then translation comes from a cat/member line
                    if cat_mem == 'cat':
                        text = text.strip(': ') + ': '
                        if text[0] == '*':
                            text.replace(': ', ':* ')
                        self.lines[l_idx].output = text + self.lines[l_idx].output
                    elif cat_mem == 'member':
                        self.lines[l_idx].output += text

                except IndexError:
                    # If here, then line is a standard line
                    self.lines[l_idx].output = text
                    pass

        return [Formatter(line).run() for line in self.lines]

    def direct_translation(self, line, l_idx):
        tr_reps = diag.translate(line.source)
        tr_rep = tr_reps[0]
        if tr_rep[0]:
            line.output = tr_rep[1] + tr_rep[2]
            line.ok = True
            if len(tr_reps[1:]) > 0:
                line.alt += [tr[1] for tr in tr_reps[1:]]
        else:
            line.save = True
            self.trans_w_google.append((l_idx, line))
            # line.output = self.google_translate(line.source)
            line.commands.append('google_translation')

    def cat_translation(self, line, l_idx):
        ocrs = diag.translate(t.get_cat(line.source))   # ocrs = output cat reports [[bool:translation_success,translation,flag,order],...] translate always returns, so ocrs[0] won't fail
        ocr = ocrs[0]
        o_cat = ocr[1].strip(': ') + ': '   # removes trailing ': ' and even ':'  removing and adding, to make sure there is always only one.

        omrs = diag.translate(t.get_cat_member(line.source))    # omr = output member report
        omr = omrs[0]
        o_member = t.cap_first(omr[1].strip())

        if ocr[0] and len(ocr[2]) > 0:
            line.commands.append('cat_' + ocr[2].strip('\t'))
        if omr[0] and len(omr[2]) > 0:
            line.commands.append('member_' + omr[2].strip('\t'))

        line.output = ''
        if ocr[0]:  # if successful cat translation
            if o_cat[0] == '*':
                o_cat = o_cat.replace(': ', ':* ')
            line.output += o_cat
            if len(ocrs) > 1:
                line.alt += list(set([tr[1] for tr in ocrs[1:]]))
        else:
            line.save = True
            line.commands.append('cat_new')
            self.trans_w_google.append((l_idx, o_cat, 'cat'))

        if omr[0]:  # if successful member translation
            line.output += o_member
            if len(omrs) > 1:
                line.alt += list(set([tr[1] for tr in omrs[1:]]))
        else:
            line.save = True
            line.commands.append('member_new')
            self.trans_w_google.append((l_idx, o_member, 'member'))

        if ocr[0] and omr[0]:
            line.ok = True   # if both translations were successful, mark line as ok.


    def by_word_translation(self,src=None):
        if src is None:
            src = self.line.source
        src = t.decimal_replace(src)
        lookup_words = src.split(' ')
        out_words = ' '.join([diag.translate(word)[0][1] for word in lookup_words])
        return t.nest(out_words,t.cap_first,t.fds,t.decimal_replace)

    def google_translate(self, lines_text):
        project_id = os.environ.get('PROJECT_ID')
        client = translate.TranslationServiceClient()
        parent = f"projects/{project_id}/locations/global"

        response = client.translate_text(
            contents = lines_text,
            target_language_code = 'en',
            source_language_code = 'de',
            parent = parent,
        )

        translations = [G_Formatter(html.unescape(trsltn.translated_text)).run()
                        for trsltn in response.translations]

        return translations

class Processor(object):
    def __init__(self, line, inp):
        self.line = line
        self.input = inp.split('\t')[0]
        self.message = ''
        self.commands = self.get_commands(inp) #maybe here could be a sorting the order of commands, such that the save command would be last.
        self.active_command = None
        self.com_table = {
            'new_translation'         :   self.missed_line,
            'cat_new'                 :   self.missed_line,
            'google_translation'      :   self.missed_line,
            'member_new'              :   self.missed_line,
            'cat_order_corrupted'     :   self.missed_line,
            'member_order_corrupted'  :   self.missed_line,
            'order_corrupted'         :   self.missed_line,
            'replaced'                :   self.missed_line,
            'lowered'                 :   self.missed_line,
            'save'                    :   self.save,
            'lb'                      :   self.lb,
            'show'                    :   self.show,
            'retry'                   :   self.retry,
            'll'                      :   self.lower_list,
            'la'                      :   self.lower_all
            # 'lower'                   :   self.lower,
            # 'lw'                      :   self.learn_words,
            # 'oc'                      :   self.only_cat,
            # 'om'                      :   self.only_member
            # 'rep'                     :   self.alternate_row
        }

    def run(self):
        # self.line.history.append(self.input)
        if self.commands:
            if any([cmd not in self.com_table for cmd in self.commands]) and not any(['lw' in cm for cm in self.commands]):
                print('processor commands:',self.commands)
                self.unknown_command()
            else:
                self.run_commands()
                self.line.output = self.input + self.message
        else:
            self.line.ok = True
            self.line.commands = []
            self.line.output = self.input
        return self.line


    def run_commands(self):
        for cmd in self.commands[:]:
            self.active_command = cmd
            self.commands.remove(cmd)
            self.com_table[cmd]()

    # def run_command(self,cmd):
        # if 'lw' in cmd:
        #   self.com_table['lw'](cmd.replace('lw',''))
        # elif 'rep' in cmd:
        #   self.com_table['rep'](cmd.replace('rep',''))
        # else:

    def missed_line(self):
        self.message = '\t%s --> MISSED'%self.active_command

    def lb(self):
        self.line.prefix = '@+'
        self.line.suffix = '@+@+'
        # if len(self.line.output.split('\t')) == 1:
        #   self.line.ok = True

    def show(self):
        self.message += '\tt_method_used: '+self.line.t_method

    def retry(self):
        new_line = Lator(Line(self.line.source)).run()
        new_line.prefix = self.line.prefix
        self.line = new_line
        self.input = self.line.output
        # self.message = '\tretry'

    # def lower(self):
    #   print(self.input)
    #   print(self.line.output)
    #   tmp = self.input
    #   self.input = tmp[0]+tmp[1::].lower()

    def save(self, article):
        self.line.save = True

    def lower_list(self):
        lower_leading_words = re.compile(r",?\s?([A-Za-z\s]+?,)")
        lower_last_word = re.compile(r",\s?[a-zA-Z]+?\s{1}")
        self.input = lower_leading_words.sub(lambda pat: pat.group(0).lower(),self.input)
        self.input = lower_last_word.sub(lambda pat: pat.group(0).lower(),self.input)
        self.message = '\tlowered'

    def lower_all(self):
        self.input = t.capitalize_first_letter(self.input)
        self.input = t.upper_case_after_colon(self.input)
        self.message = '\tlowered'

    # def learn_words(self,arg_string):
    #   self.line.output = self.input
    #   comms = [cm for cm in self.commands if 'lw' not in cm]
    #   self.line.commands = ''.join(comms)
    #   args = [[[int(idx)-1 for idx in idxs.split('+')] for idxs in arg.split('-')] for arg in arg_string.split(',')]
    #   for pair in args:
    #     inp  = ' '.join([self.line.source.split(' ')[idx] for idx in pair[0]])
    #     outp = ' '.join([self.line.output.split(' ')[idx].strip(',') for idx in pair[1]])
    #     diag.save_word(inp,outp)
    #   self.line.ok = True

    # def only_cat(self):
    #   if self.line.t_method == 'cat':
    #     self.line.t_method += '_cat'
    #   else:
    #     self.message += 'oc only works on lines with one :'

    # def only_member(self):
    #   if self.line.t_method == 'cat':
    #     self.line.t_method += '_member'
    #   else:
    #     self.message += 'om only works on lines with one :'

    def alternate_row(self,digs):
        row_nums = digs.split('+')
        new_row = ': '.join([self.line.alt.pop(idx) for idx in row_nums])
        self.line.alt.append(self.line.output.split('\t')[0]+'\treplaced')

    def unknown_command(self):
        if "Not_recognized" in self.commands:
            self.message = self.commands
        else:
            self.message = '\t%s\tNot_recognized'%'\t'.join(self.commands)

    def get_commands(self,str):
        #maybe here could be a sorting the order of commands
        if '\t' in str:
            return str.split('\t')[1:]
        else:
            return None

class G_Formatter(object):
    def __init__(self,input_string):
        self.input = input_string

    def run(self):
        self.regexes()

        for key in GOOGLE_API_REPLACEMENT_DICT.keys():
            self.output = self.output.replace(key, GOOGLE_API_REPLACEMENT_DICT[key])

        return self.output

    def regexes(self):
        self.output = t.nest(t.format_article_nr(self.input),
                                                 t.remove_space_between_digit_and_inch_sign,
                                                 t.capitalize_first_letter,
                                                 t.upper_case_after_colon)


class Formatter(object):
    """docstring for Formatter"""
    def __init__(self, line):
        self.line = line

    def run(self):
        self.auto_case()
        self.line.output = t.nest(t.restore_upper(self.line.source,self.line.output),
                                                            t.cap_first,
                                                            t.decimal_replace,
                                                            t.cap_word_after_nums)
        self.line.output = t.thousands_replace(self.line.output).replace('Approx.','approx.')

        if self.line.type == 'title':
            self.capitalise_title()

        return self.line

    def auto_case(self):
        res = []
        for word in self.line.output.split(' '):
            if word in UPPER_CASE_WORDS:
                res.append(word.capitalize())
            else:
                res.append(word)
        self.line.output = ' '.join(res)

    def capitalise_title(self):
        capitalised_words = []
        for word in self.line.output.split(' '):
            if word in NON_CAP_TITLE_WORDS or word.isupper():
                capitalised_words.append(word)
            elif '-' in word:
                word = '-'.join([part.capitalize() for part in word.split('-')])
                capitalised_words.append(word)
            elif word[0] == '(' and word[-1] == ')':
                capitalised_words.append('({})'.format(word[1:-1].capitalize()))
            else:
                capitalised_words.append(word.capitalize())
        self.line.output = ' '.join(capitalised_words)



