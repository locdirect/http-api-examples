# http-api-examples
Python examples of how to use LocalizeDirect's localization tool LocDirect HTTP(s) API usage 

Download the LocDirect API documentation [here](http://localizedirect.com/locdirect_downloads/)

* Create project "SwedishSource"

Add English and Swedish languages
Set Swedish as source language

Add two strings:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_0.png)

* Create project "EnglishSource"

Add English and French languages
Set English as source language

* Add API user 

Make it a development type of user

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_1.png)

Edit both projects and add the user as "Project Member(s)":

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_2.png)



##EXPORTER SCRIPT

Lets try out the exporter command ld_http_exporter.py
It has the following arguments:

```
  -h, --help            show this help message and exit

  -u USER, --user USER  User name

  -pw PASSWORD, --password PASSWORD

                        Password

  -p PROJECT, --project PROJECT

                        Project name

  -s SERVER, --server SERVER

                        Server address

  -f FORMAT, --format FORMAT

                        csv or json

  -o OUTPUT, --output OUTPUT

                        Output file name
```

```
python ld_http_export.py -u USERNAME -pw SECRET -p SwedishSource -s http://SERVER:50700/api/v1 -f csv -o test.csv
```

This generates a UTF-8 formatted csv that looks like:
```
"Strings/","str_1","Hejsan","Hello"

"Strings/","str_2","""qoute test""",""
```


Notice how the " comes out as “" we use double quotations for managing quotes in csv.

Running the same but using json as format instead of csv generates:

```json
[
    {"text_enUS": "Hello", "path": "Strings/", "sourceLanguageText": "Hejsan", "identifierName": "str_1"}, 
    {"text_enUS": "", "path": "Strings/", "sourceLanguageText": "\"qoute test\"", "identifierName": "str_2"}
]
```

Notice that in json the " comes out as \"

##IMPORTER SCRIPT

Now, delete the two exported strings from the SwedishSource project and we’ll import the test.csv file into the project again. The importer can only import csv files - however, you can change the script to add additional format support.

```
  -h, --help            show this help message and exit

  -u USER, --user USER  User name

  -pw PASSWORD, --password PASSWORD

                        Password

  -p PROJECT, --project PROJECT

                        Project name

  -s SERVER, --server SERVER

                        Server address

  -i INPUT, --input INPUT

                        CSV file name

  -f FIELDS, --fields FIELDS

                        Comma separated fields for each column

                        (stringId,path,text_xxXX)
```

```
 python ld_http_import.py -u USERNAME -pw SECRET -p SwedishSource -s http://SERVER:50700/api/v1 -i test.csv -f folderPath,identifierName,sourceLanguageText,text_enUS
```

This will import the two strings into the project again.

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_3.png)

##UPDATER SCRIPT

When English is not the source language of a project a usual process is to translate it into English first and then use the English as source for going into other languages. This introduces a new step in the localization process using LocDirect this can be dealt with by setting up two projects. Lets say Swedish is the source and English is the target language of the first project, named "SwedishSource". The second project then has English as source and French, Italian and Spanish as target languages. This second project is named "EnglishSource".

 To keep the text in sync we'd like to export the English from "SwedishSource" and import it into "EnglishSource" as source language. If the string already exist in "EnglishSource" AND the string has changed, we'd like to change the status of any potential translation to "out-of-date". This is the default behaviour of the string import api command. This is an example of a script that carries out the update from one project to another.

The fields input is used to copy over additional fields such as description or custom fields.

The language input should be the language and country code for the target language in the source project and the language you wish to make the source in the second project. In our example that would be English, so the input should be enUS

```
  -h, --help            show this help message and exit

  -u USER, --user USER  User name

  -pw PASSWORD, --password PASSWORD

                        Password

  -fp FROMPROJECT, --fromProject FROMPROJECT

                        from Project name

  -fs FROMSERVER, --fromServer FROMSERVER

                        from Server address

  -tp TOPROJECT, --toProject TOPROJECT

                        to Project name

  -ts TOSERVER, --toServer TOSERVER

                        to Server address

  -l LANGUAGE, --language LANGUAGE

                        Language code that will become source language in

                        destination project

  -f FIELDS, --fields FIELDS

                        Semicolon separated fields with additional columns to
```

SwedishSource project looks like this:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_4.png)

And EnglishSource is empty:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_5.png)

python ld_http_updater.py -u USERNAME -fp SwedishSource -tp EnglishSource -pw SECRET -l enUS -f description -fs http://SERVER:50700/api/v1 -ts [http://SERVER:50700/api/v1](http://server:50700/api/v1)

Will output:

```
Logging in api on source server

Logging in api on destination server

Updating 1 strings

Strings imported
```


And EnglishSource will look like (you may have to give the client some time to refresh or click the client refresh icon ![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_6.png)):

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_7.png)

So str_1 which was translated into English has now appeared in EnglishSource and the English text is now used as source language ready to be localized into other languages.

Lets type in the French translation into EnglishSource:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_8.png)

Lets make a change to SwedishSource:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_9.png)

And run the ld_http_updater script again. This outputs:

```
Logging in api on source server

Logging in api on destination server

No strings to update, exiting
```

As the str_1 source was changed the translation status of enUS was changed to "out-of-date" only fully translated strings are moved. Lets update the English translation in SwedishSource:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_10.png)

Run the ld_http_updater script again. This outputs:

```
Logging in api on source server

Logging in api on destination server

Updating 1 strings

Strings imported
```

And EnglishSource now looks like:

![image alt text](https://raw.github.com/locdirect/http-api-examples/master/images/image_11.png)

The English source text has changed and the status of any existing translations have changed to "out-of-date"

If you plan to use the updater script for your project here’s a few things to know:

Folders will be created in the destination project but if the source project folder name is renamed, one of two things will happen:

If you use the project setting "String Identifiers must be unique in project" then the the renamed folder will be created in the destination project but any existing strings that already had been added to the destination will stay in their original folder. This behaviour may change in later versions. 

If you have unchecked the  "String Identifiers must be unique in project" and allow non-unique ID then the new folder will be created and a new instance of the string will also be created. Any existing strings in the old folder will remain. This will lead to duplicates.

So, if folders are used - they should not be changed, nor should strings be moved out of their folders. If a folder is renamed, then the destination folder should be renamed manually before executing any update.


