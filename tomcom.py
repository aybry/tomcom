# -*- coding: utf-8 -*-
#!/usr/bin/python
import os
import sys
import time
import shutil
from urllib.error import HTTPError
from lib.tools import get_config
from lib.classes import *
from lib.agents import dictionary
import lib.agents.storage as stag


def main(main_window, manual_url=None):

    def translate_article():
        for idx, line in enumerate(article.l_obj_ary):
            ta = Lator(line)
            article.l_obj_ary[idx] = ta.run()
        translation_in_progress = not article.ready()
        return translation_in_progress

    def process_input(user_input_rows):
        if len(article.l_obj_ary) != len(user_input_rows):
            print('\n' + 'Warning'.center(40, '=') +
                  '\nThe number of entered translations (%s) is not equal to the number of rows in the article (%s).' % (len(user_input_rows), len(article.l_obj_ary)) +
                  '\n' + 'Warning'.center(40, '='))
        if article.src_was_formatted:
            for idx, line in enumerate(article.l_obj_ary):
                article.l_obj_ary[idx] = Processor(line, user_input_rows[idx]).run()
            translation_in_progress = not article.ready()
        else:
            article.l_obj_ary = []
            for idx, line in enumerate(user_input_rows):
                if idx == 0:
                    prefix = '@!'
                else:
                    prefix = '@@'
                suffix = ''
                article.l_obj_ary.append({'prefix': prefix,
                                          'suffix': suffix,
                                          'source': '',
                                          'output': line,
                                          'save': False})
                translation_in_progress = False
            article.finished = True
        return translation_in_progress

    def save_article():
        try:
            entries = []

            for line in article.l_obj_ary:
                if line.ok and line.save:
                    entry = dictionary.process_line(line)
                    if entry is not None:
                        entries.append(entry)

            dictionary.save(entries)

        except AttributeError:
            pass

    def engage_wait_loop(wait_type, sec=1, art_no=None):
        def url():
            old_url = main_window.url
            present_url = main_window.get_article_url()
            return old_url == present_url

        def file():
            output, _ = stag.load_worker_files()
            output = chop_alternatives(output)
            return (output[-1] not in ['p', 's', 'q', 'n', 'lo', 'r'] and 'wait' not in output[-1])

        if art_no is not None:
            get_stats(art_no)

        sel = {'url': url, 'file': file}
        checker = sel[wait_type]
        loop = True
        while loop:
            loop = checker()
            time.sleep(sec)

    def chop_alternatives(lary):
        tmp = ['Alternative Translations' in row for row in lary]
        if any(tmp):
            lary = [row for row in lary[:tmp.index(True)] if len(row.strip()) > 0]
        return lary

    # def sublime():
    #     if platform.system() == 'Darwin':
    #         try:
    #             mac_show('com.sublimetext.2')
    #         except:
    #             mac_show('com.sublimetext.3')
    #     elif platform.system() == 'Windows':
    #         win_show('Sublime')

    def print_income(res):
        res_len = str(len(res))
        money = str(round(len(res) / float(180), 2))
        print("\n%s characters -> %s" % (res_len, money))

    def get_stats(art_no):
        time.sleep(0.2)
        with open('data/from_date.txt', 'r') as f:
            from_date = f.read()
        today_date = date.today().strftime('%Y-%m-%d')
        stats_url = 'https://language.thomann.de/index.php?controller=statistics&action=display&performanceTimeRange='
        today_suffix = '{0}+-+{1}&date_from={0}&date_to={1}'.format(today_date, today_date)
        total_suffix = '{0}+-+{1}&date_from={0}&date_to={1}'.format(from_date, today_date)
        myauth = ('language', 'awesumpassword123')
        jar = requests.cookies.RequestsCookieJar()
        cookies = get_cookies()[0]
        jar.set('PHPSESSID', cookies['value'], domain=cookies['domain'])
        r_tdy = requests.get(stats_url + today_suffix, auth=myauth, cookies=jar)
        r_ttl = requests.get(stats_url + total_suffix, auth=myauth, cookies=jar)
        try:
            with open('data/stats.txt', 'r') as f:
                char_last = int(f.read())
        except:
            char_last = 0
        seconds = 0
        char_hour = 0
        with open('data/statslog.txt', 'r') as f:
            all_lines = f.readlines()[::-1]
            seconds_first = float(all_lines[0].split()[0])
            for line in all_lines[0:]:
                seconds_curr = float(line.split()[0])
                seconds = seconds_first - seconds_curr
                if seconds > 3600:
                    break
                char_hour += int(line.split()[1])
        try:
            char_tdy = int(get_char_num(r_tdy))
            char_ttl = get_char_num(r_ttl)
        except IndexError:   # Two sets of cookies being saved
            all_cookies = get_cookies()
            with open('data/cookies.json', 'w') as f:
                json.dump([all_cookies[-1]], f,
                           indent=4,
                           separators=(',', ':'))  # take last one
            get_stats(art_no)
            return
        char_now = char_tdy - char_last
        char_hour += char_now
        print('\nLast:\t' + str(char_now) + '\t' + str(round(char_now / 180., 2))
              + '\nHour:\t' + str(char_hour) + '\t' + str(round(char_hour / 180., 2))
              + '\nToday:\t' + str(char_tdy) + '\t' + str(round(char_tdy / 180., 2))
              + '\nTotal:\t' + str(char_ttl) + '\t' + str(round(char_ttl / 180., 2)))
        with open('data/stats.txt', 'w+') as f:
            f.write(str(char_tdy))
        if char_now > 0:
            with open('data/statslog.txt', 'a+') as f:
                f.write('{}\t{}\t{}\n'.format(round(time.time()), char_now, art_no))

    def get_char_num(pagehtml):
        soup_html = BeautifulSoup(pagehtml.text, 'html.parser')
        char_num_elem = soup_html.find_all('tr', class_='active')[0]
        loc1 = str(char_num_elem).find('%') + 11
        loc2 = str(char_num_elem)[loc1:].find('<') - 1
        num_list = str(char_num_elem)[loc1:loc1 + loc2].split('.')
        try:
            return int(''.join(num_list))
        except ValueError:
            return 0

    def get_cookies():
        return stag.jsonLoad('data/cookies.json')

    if not main_window.logged_in():
        main_window.quit()
        main_window = Browser(CONF, manual_url)

    art_no = main_window.get_article_no()
    url = main_window.remember_article_url()
    try:
        article = Article(url)
    except HTTPError:
        input('''
*********************************************************
Article not found! Skip article manually and press enter.
*********************************************************''')
        url = main_window.remember_article_url()
        article = Article(url)
    translation_in_progress = translate_article()
    if not translation_in_progress:
        res = article.art_str(True, "output")
        res = article.final_checks(res)
        main_window.del_prev_translation()
        main_window.paste_translation(res)
        print('\nPasted to browser.')
        # main_window.show()
        engage_wait_loop('url', 0.2, art_no)
        return True
    while translation_in_progress:
        stag.save_worker_files(article)
        print('\nDone! You can translate now.')
        if not article.src_was_formatted:
            print('\nWarning: No formatting in German version. Text was separated automatically!')
        engage_wait_loop('file', 0.2, art_no) # only stops if there is a 'p', 'q', 'n', 'lo', 'wait' or 's' in the last row (paste, quit, next, logout and save)

        translated_lines, inp = stag.load_worker_files()
        translated_lines = chop_alternatives(translated_lines)
        cmd = translated_lines.pop(-1)
        if cmd in ['q', 'n', 'lo'] or 'wait' in cmd:
            translation_in_progress = False
        else:
            translation_in_progress = process_input(translated_lines)

    if article.ready() or article.finished:
        res = article.art_str(True, "output")
        res = article.final_checks(res)
        save_article()
        print('\nPasted to browser.')

    if cmd == 'p' or cmd == 'e':
        # main_window.show()
        main_window.del_prev_translation()
        main_window.paste_translation(res)
        engage_wait_loop('url', 0.2, art_no)
        # get_stats(art_no)
        return True
    elif cmd == 's':
        # main_window.show()
        # main_window.refresh()
        main_window.del_prev_translation()
        main_window.paste_translation(res)
        main_window.submit_translation()
        # get_stats(art_no)
        return True
    elif cmd == 'n':
        main_window.skip_article()
        return True
    elif cmd == 'lo':
        main_window.logout()
        return False
    elif cmd == 'q':
        main_window.quit()
        return False
    elif cmd == 'r':
        print('\nReloading article page...')
        return True
    elif 'wait' in cmd:
        start = time.time()
        try:
            mins = re.search(r"\d+", cmd).group(0)
        except:
            print("couldn't recognize how long to wait, will wait two hours as default")
            mins = 120
        print('Starting to wait %s minutes... press ctrl+c to continue.'%mins)
        i=0
        try:
            while time.time() - start < int(mins) * 60:
                time.sleep(600)
                print('waiting')
                main_window.save_cookies()
                main_window.refresh()
                i += 1
        except KeyboardInterrupt:
            print('\nI waited '+str(round((time.time()-start)/60, 2))+'minutes for you.\nPlease restart the script, your session should still be live')
            return False


if __name__ == "__main__":
    print('TomCom started')
    main_loop = True
    if not os.path.exists(stag.CONF_PATH):
        config = get_config()
        print('Setup finished. Tomcom will now restart with your config. Thank you.')
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        config = stag.CONF
        # main_loop = False # remove line to enable tomcom

    if not os.path.exists(stag.COOKIE_PATH):
        stag.jsonSave(stag.COOKIE_PATH, [])
    if not os.path.exists(stag.OWN_DICT_PATH):
        shutil.copyfile(os.path.join(stag.DBF, stag.OWN_DICT_NAME), stag.OWN_DICT_PATH)

    try:
        main_window = Browser(config, sys.argv[1])
    except IndexError:
        main_window = Browser(config)

    print('TomCom is running.\nIf you want to quit, add a line with the letter q to your translation and save.\nHit ctrl+c at any time to terminate hard')
    while main_loop:
        main_loop = main(main_window)
    print('Good Bye!')