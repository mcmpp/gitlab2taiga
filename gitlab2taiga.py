import ujson
import pandas as pd
import requests
import json
import sys, getopt
import getpass

# endpoint mandatory

def main(argv):
    try:
        opts, args = getopt.getopt(argv,"h:i:m:e:u",["="])
    except getopt.GetoptError:
        print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username>')
        sys.exit(2)
    if not opts:
        print ('gitlab2taiga.py')
    else:
        for opt, arg in opts:
            if opt == '-h':
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username>')
                sys.exit()
            elif opt in '-i':
                if (arg != null)
                    #importIssues(arg)
                    print ('issues file : ', arg)
            elif opt in '-m':
                if (arg != null)
                    #importIssues(arg)
                    print ('members file : ', arg)
            elif opt in '-e':
                if (arg != null)
                    #importIssues(arg)
                    print ('endpoint : ', arg)
            elif opt in '-u':
                if (arg != null)
                    #importIssues(arg)
                    print ('usename : ', arg)
            else:
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username>')


def importIssues(issues, members ):
    records = map(ujson.loads, open(path_issues, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    pd.set_option("display.max_rows", None, "display.max_columns", None,'display.max_colwidth', None)
    #print(df.keys())
    #print(df[['title','description','author_id']])
    print(df[['description']].head(15))
    #print(df.iloc[2])


def getAccessToken(endpoint):
    password = getpass.getpass()
    response = requests.get(endpoint)
    print(response)
