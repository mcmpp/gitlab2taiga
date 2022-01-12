#!/usr/bin/env python3

import ujson
import pandas as pd
import requests
import json
import sys, getopt
import getpass
import validators

ENDPOINT_PROJECTS = "/api/v1/projects"
ENDPOINT_MEMBERS = "/api/v1/memberships"
ENDPOINT_ROLES = "/api/v1/roles"
ENDPOINT_LOGIN = "/api/v1/auth"

def main(argv):
    try:
        opts, args = getopt.getopt(argv,'hi:m:e:u:p:')
    except getopt.GetoptError:
        print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        sys.exit(2)
    if len(opts) != 5:
        print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        sys.exit(2)
    else:
        for opt, arg in opts:
            if opt == '-h':
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
                sys.exit()
            elif opt in '-i':
                issues_file = arg
            elif opt in '-m':
                members_file = arg
            elif opt in '-e':
                endpoint = arg
            elif opt in '-u':
                username = arg
            elif opt in '-p':
                projectName = arg
            else:
                print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')
        if (username is not None) and (issues_file is not None) and (members_file is not None) and (endpoint is not None) and (projectName is not None):
            if (validators.url(endpoint)):
                getAccessToken(username, issues_file, members_file, endpoint)
                createProject(endpoint, projectName)
                createMemberships(endpoint, members_file)

            else:
                print ('The endpoint provided is not a valid url')
                exit (2)
        else:
            print ('gitlab2taiga.py -i <issues file> -m <members file> -e <taiga endpoint> -u <taiga username> -p <project name>')

def getAccessToken(username, issues_file, members_file, endpoint):
    print('Please, introduce the password to connect to taiga username already provided')
    global password
    password = getpass.getpass()
    data = {}
    data['password'] = password;
    data['type'] = 'normal';
    data['username'] = username;
    response = requests.post(endpoint + ENDPOINT_LOGIN, data = data)
    if response.ok:
        responseJson = response.json()
        try:
            global authToken
            authToken = responseJson['auth_token']
            print ('Auth token request successful')
        except:
            print ('We could not get the authorization token from the login request')
            exit (2)
    else:
        print ('The response from the server is not valid')
        exit (2)

def prepareHeaders():
    if (authToken is not None):
        return {"Authorization": "Bearer " + authToken}
    else:
        print ('The auth token is not correct')
        exit (2)

# ----------------   MEMBERSHIPS

def getMemberships(issues_file, members_file, endpoint):
    response = requests.get(endpoint + ENDPOINT_MEMBERS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            memberName = []
            for membership in responseJson:
                memberName.append(membership['full_name'])
            print ('Current memberships are: ' , memberName)
            return memberName
        except:
            print ('We could not get the memberships full name')
    else:
        print ('The response from the server is not valid')
        exit (2)

def getMembershipsFromGitlabFile(members_file, endpoint):
    records = map(ujson.loads, open(members_file, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    test = df[['user','access_level']]
    values = []
    for user in test.values.tolist():
        if (int(user[1]) >= 40):
            data = {}
            data['project'] = projectId
            data['username'] = user[0]['username'] + '@tegonal.com'
            data['role'] = getStakeholderRole(endpoint)
            values.append(data)
    return(values)

def createMemberships(endpoint, members_file):
    memberships = getMembershipsFromGitlabFile(members_file, endpoint)
    for member in memberships:
        if not membershipExists(endpoint, member['username']):
            response = requests.post(endpoint + ENDPOINT_MEMBERS, data = member, headers = prepareHeaders())
            if response.ok:
                print ('Member ', member['username'], ' created')
            else:
                print ('The response from the server while creating the memberships is not valid')
                exit (2)
        else:
            print ('The member ', member['username'], ' already exists')

def membershipExists(endpoint, memberName):
    memberIds = getMembershipIds(endpoint, memberName)
    for memberId in memberIds:
        response = requests.get(endpoint + ENDPOINT_MEMBERS + '/' + str(memberId), headers = prepareHeaders())
        if response.ok:
            responseJson = response.json()
            try:
                if responseJson['email'] == memberName:
                    return True
            except:
                print ('We could not get the member email')
        else:
            print ('The response from the server is not valid')
            exit (2)
    return False

def getMembershipIds(endpoint, memberName):
    response = requests.get(endpoint + ENDPOINT_MEMBERS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            memberIds = []
            for membership in responseJson:
                memberIds.append(membership['id'])
            return memberIds
        except:
            print ('We could not get the member id')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  ROLES

def getStakeholderRole(endpoint):
    response = requests.get(endpoint + ENDPOINT_ROLES + '?project=' + str(projectId), headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            for role in responseJson:
                if role['name'] == 'Stakeholder':
                    return role['id']
        except:
            print ('We could not get the roles')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  PROJECT

def createProject(endpoint, projectName):
    global projectId
    projectId = projectNameExists(endpoint, projectName)
    if projectId == 0:
        data = {}
        data['description'] = "Gitlab import from " + projectName
        data['name'] = projectName
        response = requests.post(endpoint + ENDPOINT_PROJECTS, data = data, headers = prepareHeaders())
        if response.ok:
            responseJson = response.json()
            projectId = responseJson['id']
            print ('The project ' , projectName , ' with id= ' , projectId , 'has been created')
        else:
            print ('The response from the server is not valid')
            exit (2)
    else:
        print ('The project already exists')

def projectNameExists(endpoint, projectName):
    response = requests.get(endpoint + ENDPOINT_PROJECTS, headers = prepareHeaders())
    if response.ok:
        responseJson = response.json()
        try:
            for project in responseJson:
                if project['name'] == projectName:
                    return project['id']
            return 0
        except:
            print ('We could not get the project name')
    else:
        print ('The response from the server is not valid')
        exit (2)

# ----------------  ISSUES

def createIssue(issues_file, members_file, endpoint):
    if (authToken is not None):
        print (authToken)
    else:
        print ('The auth token is not correct')
        exit (2)

def importIssues(issues, members ):
    records = map(ujson.loads, open(path_issues, encoding="utf8"))
    df = pd.DataFrame.from_records(records)
    pd.set_option("display.max_rows", None, "display.max_columns", None,'display.max_colwidth', None)
    #print(df.keys())
    #print(df[['title','description','author_id']])
    print(df[['description']].head(15))
    #print(df.iloc[2])

if __name__ == "__main__":
   main(sys.argv[1:])
