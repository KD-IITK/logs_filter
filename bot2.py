from telethon import TelegramClient, events
import dotenv
import os
import logging
import random
import string
import zipfile
import rarfile
from tqdm import tqdm
from log_parser import LogParser
from db_connection import DB
import shutil
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

dotenv.load_dotenv()

bot = TelegramClient('bot', os.environ.get("API_ID"), os.environ.get("API_TOKEN")).start(bot_token=os.environ.get('BOT_TOKEN'))
db = DB(os.environ.get('DATABASE'))
# Define a dictionary to store progress data for each user
progress_data = {}

def extract_archive(file_path, user_id):
    extracted_dir = os.path.splitext(file_path)[0] + '_extracted'
    # Create the directory for the extracted files if it does not exist
    if not os.path.exists(extracted_dir):
        os.mkdir(extracted_dir)
    # Extract the archive
    if file_path.endswith('.zip'):
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Use tqdm to show the progress bar
            progress = tqdm(zip_ref.namelist(), desc='Extracting files', unit=' files')
            for file in progress:
                zip_ref.extract(file, extracted_dir)
                progress_str = progress.format_meter(n=progress.n, total=progress.total, elapsed=progress.format_dict['elapsed'])
                progress_data[user_id]['progress'] = progress_str
    elif file_path.endswith('.rar'):
        with rarfile.RarFile(file_path, 'r') as rar_ref:
            # Use tqdm to show the progress bar
            progress = tqdm(rar_ref.namelist(), desc='Extracting files', unit=' files')
            for file in progress:
                rar_ref.extract(file, extracted_dir)
                progress_str = progress.format_meter(n=progress.n, total=progress.total, elapsed=progress.format_dict['elapsed'])
                progress_data[user_id]['progress'] = progress_str
    return extracted_dir

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Send a message when the command /start is issued."""
    await event.respond('Hello! I\'m a simple Telegram bot for filtering cloud logs.')
    raise events.StopPropagation

# Define a handler function for /progress command
@bot.on(events.NewMessage(pattern='/progress'))
async def show_progress(event):
    user_id = event.chat_id
    if user_id in progress_data:
        progress_message = progress_data[user_id]['progress']
        await event.respond(progress_message)
    else:
        await event.respond('No active downloads.')
    raise events.StopPropagation

@bot.on(events.NewMessage(func=lambda e: e.document))
async def download_file(event):
    user_id = event.chat_id
    progress_data[user_id] = {'progress':'starting ...'}

    # Generate a random file name
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    file_name = random_string + '.' + event.document.mime_type.split('/')[-1]
    # Define a progress callback function
    async def progress_callback(current, total):
        progress_percent = current/total*100
        progress_data[user_id]['progress'] = f'Current progress: {progress_percent:.2f}%'
    # Download the file contents
    await bot.download_media(event.document, file_name, progress_callback=progress_callback)
    await event.respond('File downloaded successfully as ' + file_name + '! .. Now extracting file ...')
    if file_name.endswith('.zip') or file_name.endswith('.rar'):
        extracted_folder = extract_archive(file_name, user_id)
    await event.respond('File extracted successfully.')
    lp=LogParser(extracted_folder)
    victims=lp.parse_all()
    inserted = db.insert_victims(victims)
    await event.respond(f'Inserted {inserted} victims!')
    shutil.rmtree(extracted_folder)
    os.remove(file_name)



def main():
    """Start the bot."""
    bot.run_until_disconnected()

if __name__ == '__main__':
    main()