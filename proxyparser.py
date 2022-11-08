# -*- coding: utf-8 -*-
import sys
import re
import queue
import threading
import requests
import colorama
import json

print(colorama.Fore.CYAN + """
                ██████╗░██████╗░░█████╗░██╗░░██╗██╗░░░██╗██████╗░░█████╗░██████╗░░██████╗███████╗██████╗░
                ██╔══██╗██╔══██╗██╔══██╗╚██╗██╔╝╚██╗░██╔╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗
                ██████╔╝██████╔╝██║░░██║░╚███╔╝░░╚████╔╝░██████╔╝███████║██████╔╝╚█████╗░█████╗░░██████╔╝
                ██╔═══╝░██╔══██╗██║░░██║░██╔██╗░░░╚██╔╝░░██╔═══╝░██╔══██║██╔══██╗░╚═══██╗██╔══╝░░██╔══██╗
                ██║░░░░░██║░░██║╚█████╔╝██╔╝╚██╗░░░██║░░░██║░░░░░██║░░██║██║░░██║██████╔╝███████╗██║░░██║
                ╚═╝░░░░░╚═╝░░╚═╝░╚════╝░╚═╝░░╚═╝░░░╚═╝░░░╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝╚═════╝░╚══════╝╚═╝░░╚═╝
                by alexzai007
""")

class ProxyParser:
    # Начало
    def __init__(self):
        try:
            with open('parser_settings.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(colorama.Fore.RED + 'Проверьте наличие файла настроек!')
        self.threads = self.data['thread']
        self.timeout = self.data['timeout']
        self.output_file = self.data['output_file']
        self.proxies = []
        self.https = True
        self.source_threads = []
        self.check_website = self.data['check_website']
        self.dead = 0
        self.alive = 0
        self.q = queue.Queue()
        self.clear_log()
        self.proxy_sources = self.data['proxy_sources']

    #фигачим монали
    def clear_log(self):
        try:
            f = open(self.output_file, 'w')
        except FileNotFoundError:
            return

    #чекаем прокси
    def fetch_from_sources(self, url, custom_regex):
        n = 0
        proxy_list = requests.get(url, timeout=5).text
        proxy_list = proxy_list.replace('null', '"N/A"')
        custom_regex = custom_regex.replace('%ip%', '([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})')
        custom_regex = custom_regex.replace('%port%', '([0-9]{1,5})')
        for proxy in re.findall(re.compile(custom_regex), proxy_list):
            self.proxies.append(proxy[0] + ":" + proxy[1])
            n += 1
        sys.stdout.write(colorama.Fore.YELLOW + "{0: >5} проксей спарсил с {1}\n".format(n, url))
    
    # чекаем прокси с сурсов которые вы предоставили
    def find_proxies(self):
        for source in self.proxy_sources:
            t = threading.Thread(target=self.fetch_from_sources, args=(source[0], source[1]))
            self.source_threads.append(t)
            t.start()
        for t in self.source_threads:
            t.join()
        proxies_unique = list(set(self.proxies))
        print(colorama.Fore.GREEN + "{0: >5} прокси спарсил всего, {1} уникальные.".format(len(self.proxies), len(proxies_unique)))
        self.proxies = proxies_unique

        for x in self.proxies:
            self.q.put([x, "N/A"])


        #проверяем прокси на валид
        def check_proxies():
            while not self.q.empty():
                proxy = self.q.get()
                try:
                    resp = requests.get(("https" if self.https else "http") + ("://" + self.check_website),
                                        proxies={'http': 'http://' + proxy[0], 'https': 'http://' + proxy[0]},
                                        timeout=self.timeout)
                    if resp.status_code == 200:
                        self.alive += 1

                        with open(self.output_file, 'a') as f:
                            f.write(str(proxy[0]) + '\n')
                except:
                    self.dead += 1
                print(
                   colorama.Fore.YELLOW + "Проверил %{:.2f} - (Работает: {} - Не работает: {})".format((self.alive + self.dead) / len(self.proxies) * 100, self.alive, self.dead), end='\r')


        threads_list = []
        for i in range(0, self.threads):
            t = threading.Thread(target=check_proxies)
            t.start()
            threads_list.append(t)
        for t in threads_list:
            t.join()


        #итоговый вывод
        print(colorama.Fore.GREEN + "Завершено - Работает: {} - Не работает: {}         \n".format(self.alive, self.dead), end='\r')
        print(colorama.Fore.GREEN + "Результат сохранён в " + self.output_file)

#Запуск
ProxyParser().find_proxies()