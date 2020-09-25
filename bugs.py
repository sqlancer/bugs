import json
import argparse
import sys


parser = argparse.ArgumentParser(prog='bugs.py')
parser.add_argument('action', choices=['check', 'format'])
args = parser.parse_args()

f = open("bugs.json", "r")
original_content = f.read()
parsed_content = json.loads(original_content)

def check():
    formatted_content = json.dumps(parsed_content, indent=4) + '\n'
    correctly_formatted = original_content == formatted_content
    sys.exit(0 if correctly_formatted else -1)

def format_json():
	formatted_content = json.dumps(parsed_content, indent=4) + '\n'
	f.close()
	fw = open("bugs.json", "w")
	fw.write(formatted_content)

action = args.action
{
    'check' : check,
    'format' : format_json
}[action]()
