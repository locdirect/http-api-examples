import argparse
import json
import io
import requests
import xml.etree.ElementTree as ET
import unicodecsv as csv

# Example of how to read LocDirect project data via http api call and save as json or csv (utf-8) file
# This example will read and output the path, string ID, source language, and all target languages
#
# Requires LocDirect server version 2.9.130 or later
# Uses the http / https API interface of LocDirect
# Downloads and API documentation http://localizedirect.com/locdirect_downloads/
#
# Make sure you create a user(developer type should work in most cases) in LocDirect which is a project member of the project you want to connect to
# Usage:
# ld_http_export -u USERNAME -o outfile.csv -f csv -pw SECRET -p PROJECTNAME -s http://SERVER:50700/api/v1
# LocDirect server support both http and https please use https for secure transfers
#
#  -h, --help            show this help message and exit
#  -u USER, --user USER  User name
#  -pw PASSWORD, --password PASSWORD
#                        Password
#  -p PROJECT, --project PROJECT
#                        Project name
#  -s SERVER, --server SERVER
#                        Server address
#  -f FORMAT, --format FORMAT
#                        csv or json
#  -o OUTPUT, --output OUTPUT
#                        Output file name


parser = argparse.ArgumentParser(description='locdirect api command')
parser.add_argument('-u','--user', help='User name', required=True)
parser.add_argument('-pw','--password', help='Password', required=True)
parser.add_argument('-p','--project', help='Project name', required=True)
parser.add_argument('-s','--server', help='Server address', required=True)
parser.add_argument('-f','--format', help='csv or json', required=True)
parser.add_argument('-o','--output', help='Output file name', required=True)
args = vars(parser.parse_args())

COMPACT_ROW_SEPARATOR = u'\xaf\xaf'
COMPACT_FIELD_SEPARATOR = u'\xac\xac'

# Be careful not to send any empty newlines in the xml message as that will generate an error
def loginMessage(user,password):
    return '''<?xml version="1.0" encoding="UTF-8"?>
<EXECUTION client="API" version="1.0">
     <TASK name="Login">
         <OBJECT name="Security" />
         <WHERE>
             <userName>%s</userName>
             <password>%s</password>
         </WHERE>
     </TASK>
</EXECUTION>''' % (user, password)


def stringExportMessage(secId, projectName, fields):
    return '''<?xml version="1.0" encoding="UTF-8"?>
<EXECUTION secId="%s" client="API" version="1.0">
     <TASK name="StringExport">
         <OBJECT name="String">
            <exportFields>%s</exportFields>
         </OBJECT>
         <WHERE>
             <projectName>%s</projectName>
             <folderPaths>Strings/</folderPaths>
             <responseType>ldc</responseType>
         </WHERE>
     </TASK>
</EXECUTION>''' % (secId, fields, projectName)

def getProjectLanguagesMessage(secId, projectName):
    return '''<?xml version="1.0" encoding="UTF-8"?>
<EXECUTION secId="%s" client="API" version="1.0">
     <TASK name="GetProjectLanguages">
         <OBJECT name="Language"/>
         <WHERE>
              <projectName>%s</projectName>
         </WHERE>
     </TASK>
</EXECUTION>''' % (secId, projectName)

# return dict with languages and boolean if language is source language or not
def getLanguages(secId, projectName):
    langs={}
    data = getProjectLanguagesMessage(secId, projectName)
    r = requests.post(args['server'], data=data, timeout=60)
    tree = ET.ElementTree(ET.fromstring(r.text))
    root = tree.getroot()
    for item in root.findall('.//DATASET'):
        langs[item.find('languageCode').text + item.find('countryCode').text] = (item.find('isSourceLanguage').text == 'true')
    return langs

# returns a list with target languages only
def getTargetLanguages(secId, projectName, prep=''):
    langs=[]
    data = getProjectLanguagesMessage(secId, projectName)
    r = requests.post(args['server'], data=data, timeout=60)
    tree = ET.ElementTree(ET.fromstring(r.text))
    root = tree.getroot()
    for item in root.findall('.//DATASET'):
        if item.find('isSourceLanguage').text == 'false':
            langs.append(prep + item.find('languageCode').text + item.find('countryCode').text)
    return langs

# logs in the user and get the secId
def login(user, password):
    data = loginMessage(user, password)
    r = requests.post(args['server'], data=data,  timeout=60)

    tree = ET.ElementTree(ET.fromstring(r.text))
    root = tree.getroot()

    if root.find("./[@committed='true']") is not None:
        return root.find('.//secId').text
    else:

        print root.find(".//MESSAGE").text
        print r.text
        exit(1)

# This takes the ldc format and converts it into a python string list
def ldcToList(data):
    out = []
    for row in data[:-len(COMPACT_ROW_SEPARATOR)].split(COMPACT_ROW_SEPARATOR):
        out.append(row[:-len(COMPACT_FIELD_SEPARATOR)].split(COMPACT_FIELD_SEPARATOR))
    return out

# Format string list into dictionary using fields as keys
def listToDict(fields, data):
    strings = []
    for row in data:
        item = {}
        for idx, field in enumerate(fields):
            item[field] = row[idx]
        strings.append(item)
    return strings

def main(args):
    print "Logging in %s" % args['user']
    secId = login(args['user'], args['password'])
    languages = getTargetLanguages(secId, args['project'], 'text_')
    
    # You can change what fields to include, see API docs for available fields
    fields = 'path;identifierName;sourceLanguageText;' + ';'.join(languages)
    data = stringExportMessage(secId, args['project'], fields)
    print "Reading fields: %s" % fields
    r = requests.post(args['server'], data=data, timeout=60)
    r.encoding = 'utf-8'

    #print r.content
    stringList = ldcToList(r.text)
    if args['format'] == 'json':
        dictList = listToDict(fields.split(';'),stringList)
        with io.open(args['output'], 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(dictList, ensure_ascii=False))

    elif args['format'] == 'csv':
        #print stringList
        csvWriter = csv.writer(open(args['output'], 'w'), delimiter=',',  doublequote=True, dialect=csv.excel, quoting=csv.QUOTE_ALL, encoding='utf-8')
        csvWriter.writerows(stringList)

    else:
        print "Cant recognize format, use -f csv or json"
        exit(1)

    print "File %s saved" % args['output']

if __name__ == '__main__':
    main(args)