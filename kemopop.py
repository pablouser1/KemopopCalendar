import argparse
from datetime import date, datetime, timedelta, UTC
import polib
from os import scandir
from os.path import join
from godot_parser import load
from icalendar import Calendar, Event

FOLDERS = ['kemopop_base', 'kemopop_dlc_summer', 'kemopop_guests']

def get_character_name(character_id: str, po: polib.POFile) -> str:
    entry = po.find(f"character_{character_id}")
    if entry:
        return entry.msgstr
    
    # Fallback if not found
    return name.replace('guest_', '').capitalize()

def get_characters(path: str, po: polib.POFile) -> list:
    characters = {}

    for folder in FOLDERS:
        characters_folder = join(path, 'assets', folder, 'characters')
        subfolders = [ f.path for f in scandir(characters_folder) if f.is_dir() ]
        for subfolder in subfolders:
            scene = load(join(subfolder, 'character.tscn'))
            node = scene.get_node()
            character_group = node['character_group']
            if character_group not in characters:
                # When no birthday_month default to January
                birthday_month = node.properties.get('birthday_month', 1)
                characters[character_group] = {
                    'id': character_group,
                    'name': get_character_name(node['character_id'], po),
                    'birthday_month': birthday_month,
                    'birthday_day': node['birthday_day']
                }
    
    return list(characters.values())

def build_cal(characters: list) -> Calendar:
    now = datetime.now(UTC)
    year = now.year

    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '//Kemopop! Calendar//')

    for character in characters:
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
    
    return cal

def main(path: str, output: str, lang: str):
    po = polib.pofile(join(path, 'locale', lang, 'strings.po'))
    characters = get_characters(path, po)
    cal = build_cal(characters)

    with open(output, 'wb') as f:
        f.write(cal.to_ical())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='KemopopCal', description='Export birthdays to ics')
    parser.add_argument('path')
    parser.add_argument('-o', '--output', default='kemopop.ics', help='File output')
    parser.add_argument('-l', '--lang', default='en', help='Language for characters\' names')

    args = parser.parse_args()

    main(args.path, args.output, args.lang)
