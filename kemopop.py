from datetime import date, datetime, timedelta, UTC
from os import scandir
from os.path import join
from sys import argv
from godot_parser import load
from icalendar import Calendar, Event

FOLDERS = ['kemopop_base', 'kemopop_dlc_summer', 'kemopop_guests']

def normalize_name(name: str) -> str:
    return name.replace('guest_', '').capitalize()

def main(path: str, output: str):
    now = datetime.now(UTC)
    year = now.year
    
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '//Kemopop! Calendar//')
    characters = {}

    for folder in FOLDERS:
        characters_folder = join(path, 'assets', folder, 'characters')
        subfolders = [ f.path for f in scandir(characters_folder) if f.is_dir() ]
        for subfolder in subfolders:
            scene = load(join(subfolder, 'character.tscn'))
            node = scene.get_node()
            character_group = node['character_group']
            if character_group not in characters and node.properties.get('birthday_month') is not None:
                characters[character_group] = {
                    'id': character_group,
                    'name': normalize_name(character_group),
                    'birthday_month': node['birthday_month'],
                    'birthday_day': node['birthday_day']
                }
    
    characters_arr = list(characters.values())
    for character in characters_arr:
        start_date = date(year, character['birthday_month'], character['birthday_day'])
        end_date = start_date + timedelta(days=1)
        event = Event()
        event.add('summary', f"{character['name']}'s birthday")
        event.add('uid', f"{character['id']}@kemopop")
        event.add('dtstart', start_date)
        event.add('dtend', end_date)
        event.add('dtstamp', now)
        event.add('rrule', {'FREQ': 'YEARLY'})
        cal.add_component(event)
    
    with open(output, 'wb') as f:
        f.write(cal.to_ical())

if __name__ == '__main__':
    if len(argv) == 1:
        print('No path passed!')
        exit(1)

    main(argv[1], argv[2] if len(argv) > 2 else 'kemopop.ics')
