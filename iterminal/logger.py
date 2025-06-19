import datetime

LOG_FILE = f"iterminal_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

def log_entry(entry: str):
    with open(LOG_FILE, 'a') as f:
        f.write(entry + '\n') 