__author__ = 'chris'
import argparse
import codecs
import requests
import xml.etree.ElementTree as ET
import csv

# Example of reading a UTF-8 csv file and importing it into LocDirect
# CSV fields should all be within double quotes like:
# "Strings/","str_1","Press Start"
# if content field contains a " it should be outputted as as "" so a field ["how are you?" - he said] should read as ["""how are you?"" - he said"]
#
# Requires LocDirect server version 2.9.130 or later
# Uses the http / https API interface of LocDirect
# Download it http://localizedirect.com/locdirect_downloads/
# LocDirect server support both http and https please use https for secure transfers
#
# Make sure you create a user(developer type should work in most cases) in LocDirect which is a project member of the project you want to connect to

parser = argparse.ArgumentParser(description='locdirect api command')
parser.add_argument('-u','--user', help='User name', required=True)
parser.add_argument('-pw','--password', help='Password', required=True)
parser.add_argument('-p','--project', help='Project name', required=True)
parser.add_argument('-s','--server', help='Server address', required=True)
parser.add_argument('-i','--input', help='CSV file name', required=True)
parser.add_argument('-f','--fields', help='Comma separated fields for each column (stringId,path,text_xxXX)', required=True)
args = vars(parser.parse_args())


COMPACT_ROW_SEPARATOR = u'\xaf\xaf'
COMPACT_FIELD_SEPARATOR = u'\xac\xac'


# Be careful not to send any empty lines in the xml message as that will generate an error
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


def stringImportMessage(secId, projectName, fields, data):
    fieldData = ""
    for row in data:
        for column in row:
            fieldData += column.decode('utf-8') + COMPACT_FIELD_SEPARATOR
        fieldData +=  COMPACT_ROW_SEPARATOR
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
         </WHERE>
     </TASK>
</EXECUTION>''' % (secId, ';'.join(fields), fieldData, projectName)

# logs in the user and get the secId
def login(user, password):
    data = loginMessage(user, password)
    r = requests.post(args['server'], data=data.encode('utf-8'),  timeout=60)

    tree = ET.ElementTree(ET.fromstring(r.text))
    root = tree.getroot()

    if root.find("./[@committed='true']") is not None:
        return root.find('.//secId').text
    else:

        print root.find(".//MESSAGE").text
        print r.text
        exit(1)

def main(args):
    data = []
    fields = args['fields'].split(',')

    # Read UTF8 CSV file and check so it has same amount of columns as fields
    with open(args['input'],'r') as fin:
        reader=csv.reader(fin)
        for row in reader:
            if len(list(row)) == len(fields):
                data.append(list(row))
            else:
                print "Column mismatch"
                print fields
                print list(row)
                exit(1)

    # Login
    print "Logging in %s" % args['user']
    secId = login(args['user'], args['password'])

    # Send data
    print "Sending data to server"
    message = stringImportMessage(secId, args['project'], fields, data)
    r = requests.post(args['server'], data=message.encode('utf-8'), timeout=60)
    tree = ET.ElementTree(ET.fromstring(r.content))
    root = tree.getroot()


    if root.find("./[@committed='true']") is not None:
        print "Strings imported"
    else:
        print "Error"
        print root.find(".//MESSAGE").text
        print r.text
        exit(1)

if __name__ == '__main__':
    main(args)