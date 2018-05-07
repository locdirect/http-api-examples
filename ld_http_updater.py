import argparse
import requests
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

# When English is not the source language of a project a usual process is to translate it into English first and then
# use the English as source for going into other languages. This introduces a new step in the localization process
# using LocDirect this can be dealt with by setting up two projects. Lets say Swedish is the source and English is the
# target language of the first project, named "SwedishSource". The second project then has English as source and French
# Italian and Spanish as target languages. This second project is named "EnglishSource".
#
# To keep the text in sync we'd like to export the English from "SwedishSource" and import it into "EnglishSource"
# as source language. If the string already exist in "EnglishSource" AND the string has changed, we'd like to
# change the status of any potential translation to "out-of-date". This is the default behaviour of the string import
# api command. This is an example of a script that carries out the update from one project to another.
#
# The fields input is used to copy over additional fields such as description or custom fields.
# The language input should be the language and country code for the target language in the source project, the language you
# wish to make the source in the second project. In our example that would be English, so the input should be enUS

#
# Requires LocDirect server version 2.9.131 or later
# Uses the http / https API interface of LocDirect
# Downloads and API documentation http://localizedirect.com/locdirect_downloads/
#
# Make sure you create a user(developer type should work in most cases) in LocDirect which is a project member of the project you want to connect to


# user password fromProject toProject sourceLangField additionalFields fromServer toServer
parser = argparse.ArgumentParser(description='locdirect api command')
parser.add_argument('-u','--user', help='User name', required=True)
parser.add_argument('-pw','--password', help='Password', required=True)
parser.add_argument('-fp','--fromProject', help='from Project name', required=True)
parser.add_argument('-fs','--fromServer', help='from Server address', required=True)
parser.add_argument('-tp','--toProject', help='to Project name', required=True)
parser.add_argument('-ts','--toServer', help='to Server address', required=True)
parser.add_argument('-l','--language', help='Language code that will become source language in destination project', required=True)
parser.add_argument('-f','--fields', help='Semicolon separated fields with additional columns to be copied over', default='', required=False)

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


def stringRawImportMessage(secId, projectName, fields, data):
    return '''<?xml version="1.0" encoding="UTF-8"?>
<EXECUTION secId="%s" client="API" version="1.0">
     <TASK name="StringImport">
         <OBJECT name="String">
            <importFields>%s</importFields>
            <fieldData>%s</fieldData>
         </OBJECT>
         <WHERE>
             <stringMergeOption>3</stringMergeOption>
             <projectName>%s</projectName>
             <createFolders>true</createFolders>
         </WHERE>
     </TASK>
</EXECUTION>''' % (secId, fields, escape(data), projectName)


# logs in the user and get the secId
def login(user, password, server):
    data = loginMessage(user, password)
    r = requests.post(server, data=data.encode('utf-8'),  timeout=60)

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
    print "Logging in %s on source server" % args['user']
    secId = login(args['user'], args['password'], args['fromServer'])
    extraFields = args['fields']
    if extraFields:
        extraFields = ";" + args['fields']

    fields = 'path;identifierName;text_' + args['language'] + ';status_' + args['language'] + extraFields
    data = stringExportMessage(secId, args['fromProject'], fields)
    r = requests.post(args['fromServer'], data=data.encode('utf-8'), timeout=60)
    r.encoding = 'utf-8'
    if len(r.text) == 0 :
        print "No strings in source, exiting"
        exit(0)

    print "Logging in %s on destination server" % args['user']
    secId = login(args['user'], args['password'], args['toServer'])

    stringList = ldcToList(r.text)
    dictList = listToDict(fields.split(';'), stringList)

    prunedLDC = ""
    fields = 'folderPath;identifierName;sourceLanguageText' + extraFields
    fieldsMap = ('path;identifierName;text_' + args['language'] + extraFields).split(';')

    count = 0
    # Fields are renamed when needed, and a ldc formatted data string is created
    for item in dictList:
        # Only update if language has status 3 (translated)
        if item['status_' + args['language']] == '3':
            count += 1
            for map in fieldsMap:
                prunedLDC += item[map] + COMPACT_FIELD_SEPARATOR
            prunedLDC += COMPACT_ROW_SEPARATOR

    if count == 0:
        print "No strings to update, exiting"
        exit(0)


    print "Updating %d strings" % count
    message = stringRawImportMessage(secId, args['toProject'], fields, prunedLDC)
    r = requests.post(args['toServer'], data=message.encode('utf-8'), timeout=60)
    tree = ET.ElementTree(ET.fromstring(r.content))
    root = tree.getroot()
    if root.find("./[@committed='true']") is not None:
        print "Strings imported"
    else:
        print "Error"

        file=open('failed-message.txt','w')
        file.write(message.encode('utf-8'))
        file.close()

        print root.find(".//MESSAGE").text
        print r.text
        exit(1)

    exit(0)

if __name__ == '__main__':
    main(args)