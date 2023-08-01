import os
import configparser
from datetime import datetime
from clockable.constants import *

class Task:
    def __init__(self, start_time, end_time, description, duration: str | int | float ):
        self.start_time = start_time
        self.end_time = end_time
        self.description = description
        if isinstance(duration, str):
            self.duration = clocktime_parse(duration)
        else:
            self.duration = duration

class Session:
    def __init__(self, clock_in_time=None):
        self.clock_in_time = clock_in_time
        self.clock_out_time = None
        self.tasks = []
        self.total_session_time = None
        self.total_working_time = 0

    def add_task(self, task: Task):
        self.tasks.append(task)
        self.total_working_time += task.duration

    def clock_out(self, clock_out_time, total_session_time):
        self.clock_out_time = clock_out_time
        self.total_session_time = total_session_time

    def clockin_timestamp(self):
        return timestamp(self.clock_in_time)
    
    def clockout_timestamp(self):
        return timestamp(self.clock_out_time)

    def working_clocktime(self):
        return clocktime(self.total_working_time)
    
    def session_clocktime(self):
        return clocktime(self.total_session_time)


class Client:
    def __init__(self, full_name=None, address=None, city=None, state=None, zipcode=None, phone=None, rate: int | None =None, slug=None):
        self.full_name = full_name
        self.address = address
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.phone = phone
        self.rate: int | None  = None if rate == None else int(rate)
        self.slug = slug
        self.logs_folder = f"logs/{self.slug}"
        self.parse_fs()
    
    def parse_fs(self):
        if not os.path.exists(self.logs_folder):
            os.makedirs(self.logs_folder)
        self.logs = sorted(os.listdir(self.logs_folder), key=lambda x: os.path.getmtime(os.path.join(self.logs_folder, x)))
        self.has_logs = len(self.logs) > 0
        self.newest_log = os.path.join("logs", self.slug, self.logs[-1] if len(self.logs) > 0 else "1.log")
        self.log = Log(self) if self.has_logs else None
        self.log_writer = LogWriter(self)

    def next_log(self):
        #get the name and path of the newest log
        directory, file_name = os.path.split(self.newest_log)
        base_name, extension = os.path.splitext(file_name)
        #increment the logfile name by 1
        new_file_number = int(base_name) + 1
        new_file_name = f"{new_file_number}.log"
        #spawn the new log file
        open(os.path.join(directory, new_file_name), 'w').close()
    
    def get_all_logs(self):
        log_instances = []
        for log_file in self.logs:
            directory, file_name = os.path.split(log_file)
            base_name, extension = os.path.splitext(file_name)
            log_index = base_name
            log_instances.append(Log(self, log_index))
        return log_instances

class Log:
    def __init__(self, client: Client, log_index=None):
        self.client = client
        self.file = os.path.join(self.client.logs_folder, f"{log_index}.log") if log_index != None else self.client.newest_log
        try:
            self.parse()
        except ValueError as e:
            print(f"Error parsing log: {e}")
            print(f"Error was in file: {self.file}")

    def index(self):
        directory, file_name = os.path.split(self.file)
        base_name, extension = os.path.splitext(file_name)
        return base_name

    def parse(self):
        self.sessions:list(Session) = []
        current_session = None
        task_lines = []
        with open(self.file, 'r') as log_file:
            for line in log_file:
                line = line.strip()
                if "Clock In" in line:
                    clock_in_time = parse_timestamp(line)
                    current_session = Session(clock_in_time)
                elif "Clock Out" in line:
                    clock_out_time = parse_timestamp(line)
                    total_session_time = (clock_out_time - current_session.clock_in_time)
                    current_session.clock_out(clock_out_time, total_session_time)
                    self.sessions.append(current_session)
                    current_session = None
                elif current_session is not None:
                    task_lines.append(line)
                    if len(task_lines) == 3:
                        task = self._parse_task(task_lines)
                        current_session.add_task(task)
                        task_lines = []

    @staticmethod
    def _parse_task(lines):
        start_time, end_time = [datetime.strptime(t.strip(), "%m/%d/%Y %I:%M%p") for t in lines[0].split("-")]
        description = lines[1].strip()
        duration = lines[2].strip()
        return Task(start_time, end_time, description, duration)

class LogWriter:
    def __init__(self, client: Client):
        self.client = client

    def clock_in(self):
        self.write(f"===============[Clock In - {timestamp()}]===============\n")

    def clock_out(self):
        self.write(f"===============[Clock Out - {timestamp()}]===============\n")

    def task_finish(self, task_start_time, task_desc, task_length):
        self.write(f"\t{timestamp(task_start_time)} - {timestamp()}\n\t\t\t{task_desc}\n\t\t{task_length}\n")

    def write(self, entry):
        with open(self.client.newest_log, 'a') as f:
            f.write(entry)      

class ClientLoader:
    def __init__(self, client_book):
        self.client_book = client_book
        self.config = configparser.ConfigParser()
        self.clients = {}
        self.load()

    def load(self):
        self.config.read(self.client_book)
        for section in self.config.sections():
            client = Client(
                self.config.get(section, 'FullName', fallback=None),
                self.config.get(section, 'Address', fallback=None),
                self.config.get(section, 'City', fallback=None),
                self.config.get(section, 'State', fallback=None),
                self.config.get(section, 'Zipcode', fallback=None),
                self.config.get(section, 'Phone', fallback=None),
                self.config.get(section, 'Rate', fallback=None),
                section
            )
            self.clients[section] = client

    def client(self, slug = None) -> Client:
        if slug != None:
            return self.clients[slug] if slug in self.clients else None
        else:
            return next(iter(self.clients.values())) #return first client if none given
    
    def add_client(self, slug, full_name):
        self.config[slug] = {'FullName': full_name, 'Rate': 15.0} 
        with open(CONSTANT_CLIENTBOOK_NAME, 'w') as configfile:   
            self.config.write(configfile)
        open(os.path.join("logs", slug, "1.log"), 'w').close()
        self.clients[slug] = Client(full_name=full_name, slug=slug)