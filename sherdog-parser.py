# Python 3.7
# MMA/Sherdog scraper - enables scraping fighters data from sherdog & getting UFC's fighters roster.
# please get familiar with readme file before using!
# Created by - Montanaz0r (https://github.com/Montanaz0r)

from bs4 import BeautifulSoup
import requests
import csv
import logging
import json
import time
import concurrent.futures

# Initializes logging file.
logging.basicConfig(filename='sherdog.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
allfighters = {'fighters' : []}
MAX_THREADS = 30


class Fighter(object):
    """Fighter class - creating fighter instance based on fighter's Sherdog profile.
    """

    def __init__(self):
        """
        Initializes a Fighter instance.
        """
        self.url = None
        self.name = None  # str: fighter's name, None by default
        self.nickName = None
        self.gender = None
        self.birth_date = None
        self.height = None
        self.weight = None
        self.locality = None
        self.nationality = None
        self.weight_class = None
        self.wins = None
        self.losses = None
        self.draws = 0  # default is 0, not None because of the site layout being dynamic
        self.no_contests = 0 # default is 0, not None because of the site layout being dynamic
        self.resource = None  # setting up resource based on url, None by default
        self.soup = None  # creating BeautifulSoup object, None by default
        self.pro_range = None  # selector: selecting range to pro fights exclusively, None by default
        self.validation = False  # boolean: confirms if scraped data for fighter instance is validated, False by default


        self.association_names = None
        self.association_urls = None

        # Information about all pro fights, which certain Fighter instance had.

        self.result_data = None  # list of str: fight results
        self.opponents = None  # list of str: opponents
        self.opponent_urls = None
        self.events = None  # list of str: events
        self.events_date = None  # list of str: events date
        self.method = None  # list of str: methods in which fights have ended
        self.judges = None  # list od str: judges names
        self.rounds = None  # list of str: rounds in which fights have ended
        self.time = None  # list of str: exact point of time in the round where fights have ended

    def _set_url_from_index(self, fighter_index):
        """
        Sets up url for fighter's instance.
        :param fighter_index: integer with fighter's index
        :return: None
        """
        self.url = f'https://www.sherdog.com/fighter/index?id={fighter_index}.'

    def _set_url_from_selector(self, fighter_page):
        """
        Sets up url from css selector match.
        :param fighter_page: css selector result
        :return: None
        """
        self.url = f'http://www.sherdog.com{fighter_page}'

    def _set_resource(self):
        """
        Sets up response object based on self.url value.
        :return: response object
        """
        resource = requests.get(self.url)
        self.resource = resource
        return resource

    def _set_soup(self):
        """
        Sets up soup for Fighter's instance using data provided in self.resource.
        :return: BeautifulSoup instance
        """
        soup = BeautifulSoup(self.resource.text, features='html.parser')
        self.soup = soup
        return soup

    def set_pro_fights(self):
        """
        Sets up range of pro fights for Fighter instance with html code scraped from the site.
        :return: None
        """
        not_selected = self.soup.find_all('div', class_='module fight_history')
        for line in not_selected:
            if line.div.h2.get_text() == 'Fight History - Pro':
                pro_fights = line
                self.pro_range = pro_fights
    
    def set_name(self):
        """
        Collects and sets name for Fighter instance.
        :return: sets self.name to scraped string with fighter's name, returns AttributeError in case none was found
        """
        name = self.soup.find('span', class_='fn')
        try:
            self.name = name.get_text()
        except AttributeError:
            return AttributeError
    
    def set_nick_name(self):
        """
        Collects and sets nick_name for Fighter instance.
        :return: sets self.nick_name to scraped string with fighter's nickname, returns AttributeError in case none was found
        """
        nick_name = self.soup.find('span', class_='nickname')
        try:
            self.nickName = nick_name.get_text()
        except AttributeError:
            return AttributeError

    def set_birth_date(self):
        """
        Collects and sets birth_date for Fighter instance.
        :return: sets self.birth_date to scraped string with fighter's birthdate in ISO 8601 format, returns AttributeError in case none was found
        """
        birth_date = self.soup.find('span', itemprop='birthDate')
        try:
            self.birth_date = birth_date.get_text()
        except AttributeError:
            return AttributeError

    def set_height(self):
        """
        Collects and sets height for Fighter instance.
        :return: sets self.height to scraped string with fighter's height in imperial feet and inches, returns AttributeError in case none was found
        """
        height = self.soup.find('strong', itemprop='height')
        try:
            self.height = height.get_text()
        except AttributeError:
            return AttributeError

    def set_weight(self):
        """
        Collects and sets weight for Fighter instance.
        :return: sets self.weight to scraped string with fighter's weight in imperial pounds and lbs suffix, returns AttributeError in case none was found
        """
        weight = self.soup.find('strong', itemprop='weight')
        try:
            self.weight = weight.get_text()
        except AttributeError:
            return AttributeError

    def set_locality(self):
        """
        Collects and sets locality for Fighter instance.
        :return: sets self.locality to scraped string with fighter's city and sometimes state or region, returns AttributeError in case none was found
        """
        locality = self.soup.find('span', class_='locality')
        try:
            self.locality = locality.get_text()
        except AttributeError:
            return AttributeError

    def set_nationality(self):
        """
        Collects and sets nationality for Fighter instance.
        :return: sets self.nationality to scraped string with fighter's nationality, returns AttributeError in case none was found
        """
        nationality = self.soup.find('strong', itemprop='nationality')
        try:
            self.nationality = nationality.get_text()
        except AttributeError:
            return AttributeError
    
    def set_weight_class(self):
        """
        Collects and sets weight_class for Fighter instance.
        :return: sets self.weight_class to scraped string with fighter's most recent weight class, returns AttributeError in case none was found
        """
        item_wclass = self.soup.find('h6', class_='item wclass')
        weight_class = self.soup.find('strong', class_='title')
        try:
            self.weight_class = weight_class.get_text()
        except AttributeError:
            return AttributeError

    def set_wins_losses_draws_no_contests(self):
        """
        Collects and sets wins, losses, draws and no contests for Fighter instance.
        :return: sets self.wins, self.losses, self.draws, self.no_contests to scraped string with fighter's record attributes, returns AttributeError in case none was found
        """
        record_stats = self.soup.find_all('span', class_='counter')
        try:
            self.wins = record_stats[0].get_text()
            self.losses = record_stats[1].get_text()
            if len(record_stats) > 2:    #dynamic site layout
                self.draws = record_stats[2].get_text()
                if (len(record_stats) > 3):
                    self.no_contests = record_stats[3].get_text()
        except AttributeError:
            return AttributeError

    def set_associations(self):
        """
        Collects and sets associations for Fighter instance.
        :return: sets self.association to scraped string with fighter's gym association, returns AttributeError in case none was found
        """
        association_names = []
        association_urls = []
        try:
            finder = self.soup.find_all('a', class_='association')
            for result in finder:
                association_name = result.find('span', itemprop="name").get_text()
                association_url = result['href']
                association_urls.append(association_url)
                association_names.append(association_name)
        except AttributeError:
            logging.info(f'Attribute Error while grabbing result data for {self.name}, the data might be missing!')
        else:
            self.association_names = association_names
            self.association_urls = association_urls
            return association_names

    def grab_result_data(self):
        """
        Collects and sets results for all pro fights in range of Fighter instance.
        :return: list of strings with results
        """
        results = []
        try:
            finder = self.pro_range.find_all('span', class_='final_result')
            for result in finder:
                results.append(result.get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing result data for {self.name}, the data might be missing!')
        else:
            self.result_data = results
            return results

    def grab_opponents(self):
        """
        Collects and sets names of opponents in range of pro fights for Fighter instance.
        :return: list of strings with opponents names
        """
        fighters = []
        try:
            finder = self.pro_range.find_all('a')
            for index in range(0, len(finder), 2):
                fighters.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing opponent data for {self.name}, the data might be missing!')
        else:
            self.opponents = fighters
            return fighters

    def grab_opponent_urls(self):
        """
        Collects and sets urls of opponents in range of pro fights for Fighter instance.
        :return: list of strings with opponents urls
        """
        opponent_urls = []
        try:
            finder = self.pro_range.find_all('a')
            for index in range(0, len(finder), 2):
                opponent_urls.append(finder[index]['href'])
        except AttributeError:
            logging.info(f'Attribute Error while grabbing opponent url for {self.name}, the data might be missing!')
        else:
            self.opponent_urls = opponent_urls
            return opponent_urls

    def grab_events(self):
        """
        Collects and sets events in range of pro fights for Fighter instance.
        :return: list of strings with events
        """
        events = []
        try:
            finder = self.pro_range.find_all('a')
            for index in range(1, len(finder), 2):
                events.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing event data for {self.name}, the data might be missing!')
        else:
            self.events = events
            return events

    def grab_events_date(self):
        """
        Collects and sets events dates in range of pro fights for Fighter instance.
        :return: list of strings with events dates
        """
        events_date = []
        try:
            finder = self.pro_range.find_all('span', class_='sub_line')
            for index in range(0, len(finder), 2):
                events_date.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing event dates for {self.name}, the data might be missing!')
        else:
            self.events_date = events_date
            return events_date

    def grab_judges(self):
        """
        Collects and sets judges names in range of pro fights for Fighter instance.
        :return: list of strings with judges names
        """
        judges = []
        try:
            finder = self.pro_range.find_all('span', class_='sub_line')
            for index in range(1, len(finder), 2):
                judges.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing judges data for {self.name}, the data might be missing!')
        else:
            self.judges = judges
            return judges

    def grab_method(self):
        """
        Collects and sets fight end methods in range of pro fights for Fighter instance.
        :return: list of strings with fight end methods
        """
        methods = []
        try:
            finder = self.pro_range.find_all('td')
            for index in range(9, len(finder), 6):
                checker = 0  # small trick that will allow scraper to only get end methods and leave judge name.
                for text in finder[index].stripped_strings:
                    if checker % 2 == 0:
                        methods.append(text)
                        checker += 1
                    else:
                        checker += 1
        except AttributeError:
            logging.info(f'Attribute Error while grabbing methods data for {self.name}, the data might be missing!')
        else:
            self.method = methods
            return methods

    def grab_rounds(self):
        """
        Collects and sets information about round in which fight was finished in range of pro fights for
        Fighter instance.
        :return: list of strings with rounds
        """
        rounds = []
        try:
            finder = self.pro_range.find_all('td')
            for index in range(10, len(finder), 6):
                rounds.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing rounds data for {self.name}, the data might be missing!')
        else:
            self.rounds = rounds
            return rounds

    def grab_time(self):
        """
        Collects and sets fight time end in range of pro fights for Fighter instance.
        :return: list of strings with time
        """
        time = []
        try:
            finder = self.pro_range.find_all('td')
            for index in range(11, len(finder), 6):
                time.append(finder[index].get_text())
        except AttributeError:
            logging.info(f'Attribute Error while grabbing time data for {self.name}, the data might be missing!')
        else:
            self.time = time
            return time

    def get_validation(self):
        """
        Making validation by comparing collected data, checking if length of all information matches number of fights
        that was scraped for fighter instance.
        :return: boolean value or TypeError in case any of lists was empty (self.validation is False by default)
        """
        for_validation = [self.time, self.rounds, self.method, self.judges, self.events_date, self.events,
                          self.result_data]
        try:
            if all(len(x) == len(self.opponents) for x in for_validation):
                self.validation = True
                return True
            else:
                print(f'Warning: validation unsuccessful for {self.name}!')
                return False
        except TypeError:
            return TypeError

    def is_valid(self):
        """
        Supporting method for checking status of validation for fighter instance.
        :return: boolean value
        """
        if self.validation is True:
            return True
        else:
            return False

    def save_to_csv(self, filename):
        """
        Writing all collected information regarding fighter instance to csv file.
        :param filename: string with name of the file we want to save data to; file will be created with given name
        :return: None
        """
        with open(f'{filename}.csv', 'a', newline='', encoding="ISO-8859-1") as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            for index in range(len(self.result_data)):
                try:
                    opp = self.opponents[index]
                except IndexError:
                    opp = 'N/A'
                try:
                    result = self.result_data[index]
                except IndexError:
                    result = 'N/A'
                try:
                    event = self.events[index]
                except IndexError:
                    event = 'NA'
                try:
                    event_date = self.events_date[index]
                except IndexError:
                    event_date = 'NA'
                try:
                    method = self.method[index]
                except IndexError:
                    method = 'NA'
                try:
                    judges = self.judges[index]
                except IndexError:
                    judges = 'NA'
                try:
                    rounds = self.rounds[index]
                except IndexError:
                    rounds = 'NA'
                try:
                    time = self.time[index]
                except IndexError:
                    time = 'NA'
                try:
                    writer.writerow([self.name, opp, result, event, event_date, method, judges, rounds, time])
                except UnicodeEncodeError:
                    print(f'Coding error while attempting to save date for {self.name}, line was dropped!')
            print(f'CSV file was successfully overwritten for {self.name}!')

    def save_to_json(self, filename):
        """
        Writing all collected information regarding fighter instance to json file.
        :param filename: string with name of the file we want to save data to; file will be created with given name
        :return: None
        """
        fighter_dictionary = {self.name: []}  # initializing dictionary that will be passed into json file.
        #fighters_dict = {'fighters' : []}
        #fighter_dictionary = {}

        #fighter_dictionary['name'] = self.name
        #fighter_dictionary['nickName'] = self.nickName
        #fighter_dictionary['birthDay'] = self.birthDay
        #fighter_dictionary['fightHistoryPro'] = []
        #fighter_dictionary
        for index in range(len(self.result_data)):
            try:
                opp = self.opponents[index]
            except IndexError:
                opp = 'N/A'
            try:
                result = self.result_data[index]
            except IndexError:
                result = 'N/A'
            try:
                event = self.events[index]
            except IndexError:
                event = 'NA'
            try:
                event_date = self.events_date[index]
            except IndexError:
                event_date = 'NA'
            try:
                method = self.method[index]
            except IndexError:
                method = 'NA'
            try:
                judges = self.judges[index]
            except IndexError:
                judges = 'NA'
            try:
                rounds = self.rounds[index]
            except IndexError:
                rounds = 'NA'
            try:
                time = self.time[index]
            except IndexError:
                time = 'NA'
            line = {'opponent': opp, 'result': result, 'event': event, 'date': event_date, 'method': method,
                    'judge': judges, 'round': rounds, 'time': time}
            fighter_dictionary[self.name].append(line)
            #fighter_dictionary['fightHistoryPro'].append(line)

        #fighters_dict['fighters'].append(fighter_dictionary)

        with open(f'{filename}.json') as fighter_json:
            data = json.load(fighter_json)
        data.update(fighter_dictionary)
        #data.update(fighters_dict)
        with open(f'{filename}.json', 'w', encoding="utf-8") as fighter_json:
            json.dump(data, fighter_json, indent=4)
        print(f'JSON file was successfully overwritten for {self.name}!')
    
    def save_data(self):
        """
        Writing all collected information regarding fighter instance to json file.
        :param filename: string with name of the file we want to save data to; file will be created with given name
        :return: None
        """
        #fighter_dictionary = {self.name: []}  # initializing dictionary that will be passed into json file.
        #fighters_dict = {'fighters' : []}
        fighter_dictionary = {}

        fighter_dictionary['name'] = self.name
        fighter_dictionary['nickName'] = self.nickName
        fighter_dictionary['gender'] = self.gender
        fighter_dictionary['birthDate'] = self.birth_date
        fighter_dictionary['height'] = self.height
        fighter_dictionary['weight'] = self.weight
        fighter_dictionary['locality'] = self.locality
        fighter_dictionary['nationality'] = self.nationality
        fighter_dictionary['weightClass'] = self.weight_class
        fighter_dictionary['wins'] = self.wins
        fighter_dictionary['losses'] = self.losses
        fighter_dictionary['draws'] = self.draws
        fighter_dictionary['noContests'] = self.no_contests
        fighter_dictionary['associations'] = []
        fighter_dictionary['fightHistoryPro'] = []

        for association_index in range(len(self.association_names)):
            try:
                association_name = self.association_names[association_index]
            except IndexError:
                association_name = 'NA'
            try:
                association_url = self.association_urls[association_index]
            except IndexError:
                association_url = 'NA'
            line = {'gymName': association_name, 'gymUrl' : association_url}
            fighter_dictionary['associations'].append(line)

        #fighter_dictionary
        for index in range(len(self.result_data)):
            try:
                opp = self.opponents[index]
            except IndexError:
                opp = 'N/A'
            try:
                opponent_url = self.opponent_urls[index]
            except IndexError:
                opponent_url = 'N/A'
            try:
                result = self.result_data[index]
            except IndexError:
                result = 'N/A'
            try:
                event = self.events[index]
            except IndexError:
                event = 'NA'
            try:
                event_date = self.events_date[index]
            except IndexError:
                event_date = 'NA'
            try:
                method = self.method[index]
            except IndexError:
                method = 'NA'
            try:
                judges = self.judges[index]
            except IndexError:
                judges = 'NA'
            try:
                rounds = self.rounds[index]
            except IndexError:
                rounds = 'NA'
            try:
                time = self.time[index]
            except IndexError:
                time = 'NA'
            line = {'opponent': opp, 'opponentUrl' : opponent_url, 'result': result, 'event': event, 'date': event_date, 'method': method,
                    'judge': judges, 'round': rounds, 'time': time}
            #fighter_dictionary[self.name].append(line)
            fighter_dictionary['fightHistoryPro'].append(line)

        #fighters_dict['fighters'].append(fighter_dictionary)
        allfighters['fighters'].append(fighter_dictionary)

    def scrape_fighter(self, filetype, filename, fighter_index=None, fighter_page=None):
        """
        :param filetype: string with either 'csv' or 'json' as a type of file where results will be stored.
        :param filename: string with name of the file we want to save data to; file will be created with given name
        :param fighter_index: optional - integer with fighter's index, or None
        :param fighter_page: optional - css selector match with fighter's page, or None
        :return: True for valid fighter's page and False if page was empty
        """
        if fighter_index is not None:
            self._set_url_from_index(fighter_index)
        elif fighter_page is not None:
            self._set_url_from_selector(fighter_page)
        else:
            print("Error, please pass fighter's index, or fighter's page in order to proceed.")
        self._set_resource()
        self._set_soup()
        if self.set_name() != AttributeError:  # checking if there is existing name for a fighter instance.
            self.set_nick_name()
            self.set_birth_date()
            self.set_height()
            self.set_weight()
            self.set_locality()
            self.set_nationality()
            self.set_weight_class()
            self.set_wins_losses_draws_no_contests()
            self.set_associations()
            self.set_pro_fights()
            self.grab_result_data()
            self.grab_opponents()
            self.grab_opponent_urls()
            self.grab_events_date()
            self.grab_events()
            self.grab_judges()
            self.grab_method()
            self.grab_rounds()
            self.grab_time()
            
            if self.get_validation() != TypeError:  # if there was an empty list while validating data,
                if filetype == 'csv':               # fighter instance will be dropped.
                    self.save_to_csv(filename)
                elif filetype == 'json':
                    if(fighter_index):
                        self.save_to_json(filename)
                    else:
                        self.save_data()
            return True
        else:
            return False

# END OF FIGHTER CLASS


def scrape_all_fighters(filename, filetype='csv'):
    """
    Scrapes information about all fighters in Sherdog's database and saves them into csv or json file.
    :param filename: string with name of the file we want to save data to; file will be created with given name
    :param filetype: string with either 'csv' or 'json' as a type of file where results will be stored
    :return: None
    """
    if filetype == 'csv':
        headers = ['Fighter', 'Opponent', 'Result', 'Event', 'Event_date', 'Method', 'Referee', 'Round', 'Time']
        with open(f'{filename}.csv', 'w', newline='') as csvfile:
            init_writer = csv.writer(csvfile, delimiter=',')
            init_writer.writerow(headers)

    elif filetype == 'json':
        json_init = {}
        with open(f'{filename}.json', 'w') as fighter_json:
            json.dump(json_init, fighter_json)
            print(f'Created empty JSON file with name: {filename}')

    fighter_index = 0   # sets up and stores index of a fighter that scraper is collecting information about.
    fail_counter = 0    # amount of 'empty' indexes in a row.

    while fail_counter <= 10:  # scraper will be done after there were 10 non-existing sites (indexes) in a row.
        F = Fighter()          # creating fighter's instance object.
        scrapped_data = F.scrape_fighter(filetype, filename, fighter_index=fighter_index)
        if scrapped_data is True:
            fail_counter = 0  # resetting fail counter after finding valid page(index) for a fighter.
        else:
            fail_counter += 1  # incrementing fail counter if there was no data for certain index.
        fighter_index += 1  # incrementing index.


def scrape_ufc_roster(save='no', filetype=None):
    """
    Scrapes information about all fighters in UFC database and saves them into csv or json file.
    :param save: string with 'yes' or 'no' depends on output data allocation. Default is 'no' and data will be stored
                 only in variable
    :param filetype: string with either 'csv' or 'json' as a type of file where results will be stored. Default is None
    :return: dictionary with information about UFC roster, for each fighter there will be a tuple containing
             (name, weight-division, nickname)
    """

    scrape_start_time = time.time()
    ufc_roster = {
        'men': [],
        'women': []
    }

    men_roster = []
    women_roster = []

    def find_ufc_fighter(fighter):
        name = fighter.find('span', class_='c-listing-athlete__name').get_text().strip()
        print(f'Found {name} from UFC website...')
        division = fighter.find_all('div', class_='field__item')
        try:
            div = division[1].get_text()
        except IndexError:
            try:
                div = division[0].get_text()
            except IndexError:
                div = 'NA'
        try:
            nickname = fighter.find('span', class_='c-listing-athlete__nickname').div.get_text()
            nickname = nickname.replace('\n', '')
        except AttributeError:
            nickname = 'NA'
        if gender_index == 2:
            women_roster.append((name, div, nickname))
        elif gender_index == 1:
            men_roster.append((name, div, nickname))

    for gender_index in range(1, 3):
        page = 0
        while True:
            resource = requests.get(f'https://www.ufc.com/athletes/all?filters%5B0%5D=status%3A23&'
                                    f'gender={gender_index}&page={page}')
            soup = BeautifulSoup(resource.text, features='html.parser')
            fighters = soup.find_all('div', class_='c-listing-athlete__text')
            if len(fighters) == 0:  # if page is empty = there are no fighters left, current gender index is done.
                break
            else:
                #for index in range(len(fighter)):
                threads = min(MAX_THREADS, len(fighters))
                with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                    executor.map(find_ufc_fighter, fighters)
                page += 1

    ufc_roster['men'] = men_roster
    ufc_roster['women'] = women_roster

    scrape_end_time = time.time()
    print(f'\nFound {len(men_roster)} men and {len(women_roster)} women fighters from UFC website in {round(scrape_end_time - scrape_start_time, 2)} seconds...\n')

    if save == 'yes':
        if filetype == 'csv':
            headers = ['Name', 'Division', 'Nickname']
            with open('ufc-roster.csv', 'w', newline='') as csvfile:
                init_writer = csv.writer(csvfile, delimiter=';')
                init_writer.writerow(headers)
            with open('ufc-roster.csv', 'a', newline='', encoding="ISO-8859-1") as csvfile:
                writer = csv.writer(csvfile, delimiter=',')
                for index in range(len(ufc_roster['men'])):
                    try:
                        writer.writerow([ufc_roster['men'][index][0], ufc_roster['men'][index][1],
                                         ufc_roster['men'][index][2]])
                    except UnicodeEncodeError:
                        print(f'Unfortunately record containing {ufc_roster["men"][index]} '
                              f'dropped due to UnicodeEncodeError!')
                for index in range(len(ufc_roster['women'])):
                    try:
                        writer.writerow([ufc_roster['women'][index][0], ufc_roster['women'][index][1],
                                         ufc_roster['women'][index][2]])
                    except UnicodeEncodeError:
                        print(f'Unfortunately record containing {ufc_roster["women"][index]} '
                              f'dropped due to UnicodeEncodeError!')
        elif filetype == 'json':
            with open('ufc-roster.json', 'w') as fighter_json:
                json.dump(ufc_roster, fighter_json, indent=4)
    return ufc_roster


def scrape_list_of_fighters(fighters_list, filename, filetype='csv', gender=None):
    """
    Scrapes information about list of fighters in sherdog's database and saves them into csv or json file.
    :param fighters_list: list with fighters to be scrapped from sherdog, fighter list should contain tuple with
           (name, weight-division, nickname) for each fighter
    :param filename: string with name of the file we want to save data to; file will be created with given name
    :param filetype: string with either 'csv' or 'json' as a type of file where results will be stored. Default is 'csv'
    :return: None
    """
    number_of_failed_searches = 0
    number_of_women = None
    if(gender and len(fighters_list) == 2):
        fighters_list = fighters_list[gender]
    else:
        try:
            number_of_women = len(fighters_list['women'])
            fighters_list = fighters_list['men'] + fighters_list['women']
        except TypeError:   #normal search not entire UFC
            pass


    scrape_start_time = time.time()
    threads = min(MAX_THREADS, len(fighters_list))
    
    def search_fighter(fighter_tuple):
        """
        Nested function that creates response objects for fighter based on the information included in fighter's tuple.
        :param fighter_tuple: tuple that contains (name, weight-division, nickname) for certain fighter.
        :return: list of four response objects [1, 2, 3, 4].
                 1 - based only on fighter's name
                 2 - based on fighter's name and weight class
                 3 - based on fighter's name and nickname
                 4 - based on fighter's name, nickname and weight class
        """
        res_1 = requests.get(f'https://www.sherdog.com/stats/fightfinder?SearchTxt={fighter_tuple[0]}')
        res_2 = requests.get(f'https://www.sherdog.com/stats/fightfinder?SearchTxt={fighter_tuple[0]}'
                             f'&weight={weight_classes[fighter_tuple[1]]}')
        res_3 = requests.get(f'https://www.sherdog.com/stats/fightfinder?SearchTxt={fighter_tuple[0]}'
                             f'+{fighter_tuple[2]}')
        res_4 = requests.get(f'https://www.sherdog.com/stats/fightfinder?SearchTxt={fighter_tuple[0]}'
                             f'+{fighter_tuple[2]}&weight={weight_classes[fighter_tuple[1]]}')

        return [res_1, res_2, res_3, res_4]

    def soup_selector(request):
        """
        Nested function that makes setting up soup object and css selector for fighter instance more convenient.
        :param request: response object
        :return: css selector
        """
        soup = BeautifulSoup(request.text, features='html.parser')
        css_selector = soup.select('body > div.container > div:nth-child(3) > div.col_left > section:nth-child(2) > '
                                   'div > div.content.table > table')
        return css_selector

    def check_result(css_selector):
        """
        Nested function that makes checking for searching results based on css selector more convenient.
        :param css_selector: css selector
        :return: css selector's match, or IndexError if there is none
        """
        try:
            result = css_selector[0].find_all('a')
            return result
        except IndexError:
            return IndexError

    def create_fighter_instance(matching, index = None):
        """
        Nested function that makes creating and scraping fighter's instance object more convenient.
        :param matching: css selector results
        :return: None
        """
        fighter_page = matching[0]['href']
        F = Fighter()
        if(index and index < len(fighters_list) - number_of_women):
            F.gender = 'men'
        elif(index):
            F.gender = 'women'
        else:
            F.gender = gender
        F.scrape_fighter(filetype, filename, fighter_page=fighter_page)

    weight_classes = {
        "Heavyweight": 2,
        "Light Heavyweight": 3,
        "Middleweight": 4,
        "Welterweight": 5,
        "Lightweight": 6,
        "Featherweight": 7,
        "Bantamweight": 9,
        "Flyweight": 10,
        "Women's Strawweight": 13,
        "Women's Flyweight": 10,
        "Women's Bantamweight": 9,
        "Women's Featherweight": 7,
        "Catchweight" : 11,
    }

    if filetype == 'csv':
        headers = ['Fighter', 'Opponent', 'Result', 'Event', 'Event_date', 'Method', 'Referee', 'Round', 'Time']
        with open(f'{filename}.csv', 'w', newline='') as csvfile:
            init_writer = csv.writer(csvfile, delimiter=';')
            init_writer.writerow(headers)

    elif filetype == 'json':
        json_init = {}
        with open(f'{filename}.json', 'w') as fighter_json:
            json.dump(json_init, fighter_json)

    def scrape_fighter_data(fighter):
        index = fighters_list.index(fighter)
        print(f'Web scapring started for {fighter}')
        search_results = search_fighter(fighter)   # variable that stores different searching results.
        find_fighter = search_results[0]           # assigning first result to variable.
        selector = soup_selector(find_fighter)     # creating selector based on search result.
        results = check_result(selector)           # checking if there is a valid outcome.
        if results == IndexError:
            logging.info(f'Error occurred with {fighter}, please check carefully '
                         f'if there is no mistake in fighter name!')
        else:
            if len(results) == 1:
                create_fighter_instance(results, index)         # creating Fighter's instance and saving it.
            else:
                if( fighter[2] != 'NA'):    #if fighter has nickname (not NA), then and only then search #2 should have priority over search #3) - see Steve Garcia
                    find_fighter = search_results[2]         # assigning third result to variable.
                    selector = soup_selector(find_fighter)   # creating selector based on search result.
                    results = check_result(selector)
                    if len(results) == 1:
                        create_fighter_instance(results, index) 
                elif(fighter[2] == 'NA' or results == IndexError):
                    find_fighter = search_results[1]         # assigning second result to variable.
                    selector = soup_selector(find_fighter)   # creating selector based on search result.
                    results = check_result(selector)         # checking if there is a valid outcome.
                    if results == IndexError:
                        try:
                            find_fighter = search_results[2]         # assigning third result to variable.
                        except KeyError:
                            print('Search engine tried to narrow down findings by using weight-class filter, apparently '
                                'you have not specified weight-class data!')
                        else:
                            selector = soup_selector(find_fighter)   # creating selector based on search result.
                            results = check_result(selector)         # checking if there is a valid outcome.
                            if results == IndexError:
                                logging.info(f'Error occured with {fighter}, please check carefully if there is no mistake '
                                            f'in nickname!')
                                number_of_failed_searches += 1
                            else:
                                if len(results) == 1:
                                    create_fighter_instance(results, index)  # creating Fighter's instance and saving it.
                    else:
                        selector = soup_selector(find_fighter)        # creating selector based on search result.
                        results = check_result(selector)              # checking if there is a valid outcome.
                        if results == IndexError:
                            logging.info(f'Error occured with {fighter}, please check carefully if there is no mistake '
                                            f'in nickname!')
                            number_of_failed_searches += 1
                        else:
                            if len(results) == 1:
                                create_fighter_instance(results, index)      # creating Fighter's instance and saving it.
                            else:
                                try:
                                    find_fighter = search_results[2]  # assigning third result to variable.
                                except KeyError:
                                    print(f'Search engine tried to narrow down findings by name & nickname, apparently this'
                                        f'was not enough to find {fighter[0]}!')
                                else:
                                    selector = soup_selector(find_fighter)  # creating selector based on search result.
                                    results = check_result(selector)        # checking if there is a valid outcome.
                                    if results == IndexError:
                                        logging.info(f'Error occurred with {fighter}, please check carefully '
                                                    f'- searching with name & nickname data was unsuccessful!')
                                        number_of_failed_searches += 1
                                    else:
                                        if len(results) == 1:
                                            create_fighter_instance(results, index)  # creating Fighter's instance and saving it.
                                        else:
                                            try:
                                                find_fighter = search_results[3]  # assigning fourth result to variable.
                                            except KeyError:
                                                print(f'Search engine tried to narrow down findings by using all filters, '
                                                    f'apparently this was not enough to find {fighter[0]}!')
                                            else:
                                                # creating selector based on search result.
                                                selector = soup_selector(find_fighter)
                                                # checking if there is a valid outcome.
                                                results = check_result(selector)
                                                if results == IndexError:
                                                    logging.info(f'Error occurred with {fighter}, please check carefully '
                                                                f'- searching with all provided data was unsuccessful!')
                                                    number_of_failed_searches += 1
                                                else:
                                                    # creating Fighter's instance and saving it.
                                                    create_fighter_instance(results, index)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(scrape_fighter_data, fighters_list)
        
    scrape_complete_time = time.time()
    print(f"\nScraping {len(fighters_list)} fighter's data from Sherdog completed in {round(scrape_complete_time-scrape_start_time,2)} seconds.")

    with open(f'{filename}.json', 'w') as fighter_json:
            json.dump(allfighters, fighter_json, indent=4)
            print(f'JSON file was successfully saved for {len(fighters_list)} fighters!')

def helper_read_fighters_from_csv(filename, delimiter=','):
    """
    Helper function that will help creating fighters list from existing csv file.
    :param filename: csv filename
    :param delimiter: string with delimiter used in csv file, default = ','
    :return: list of fighters, where each fighter is a tuple(name, weight-division, nickname)
    """
    fighters_list = []
    with open(f'{filename}.csv', 'r') as csvFile:
        reader = csv.reader(csvFile)
        next(reader, None)
        for row in reader:
            str_row = f'{delimiter}'.join(row)
            split_str = str_row.split(f'{delimiter}')
            fighters_list.append(split_str)
    return fighters_list

if __name__ == '__main__':
    #scrape_all_fighters('sherdog')
    #scrape_all_fighters(filename='fighters' ,filetype="json")
    #f_list = [('Francis Ngannou', 'Heavyweight', 'NA'), ('Stipe Miocic', 'Heavyweight', 'NA')
    #, ('Tim Means', 'Welterweight', 'NA'), ('Khabib Nurmagomedov', 'Lightweight', 'NA')]
    #scrape_list_of_fighters(f_list, 'scraped_list', filetype='json')
    #scrape_list_of_fighters(ufc['men'], 'ufc-roster', filetype='json')
    ufc = scrape_ufc_roster(save='no', filetype=None)
    scrape_list_of_fighters(ufc, 'ufc-roster', filetype='json')