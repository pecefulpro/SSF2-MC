from email.mime import base
import logging
import logging.handlers
import os
import sys
import re
import json 
import config
from github import Github 
from github import Repository
from pytablewriter import MarkdownTableWriter

#Errors
from json import JSONDecodeError
from github import GithubException

def main():
    g = Github(config.github_secreat)
    repo = g.get_repo("pecefulpro/SSF2-MC")
    
   
    issue = repo.get_issue(number=6)

    if len(issue.labels) > 1:
        send_error("This issue has to many labels on it",issue)

    if issue.labels[0].name == "Update":
        update_repo(g,repo,issue)

    elif issue.labels[0].name == "Add":
        add_Repo(g,repo,issue)

    else:
        exit(0)

    

def update_repo(repo,issue):
    repolink = re.search('\\n\\n(.*)\\n\\n', issue.body).group(1)
    version = re.search('Version\\n\\n(.*)\\n\\n', issue.body).group(1)
  

def add_Repo(g,repo,issue):
    repolink = re.search("(?P<url>https?://[^\s]+)", issue.body).group("url")

    repostring = repolink.split("/")
    try:
        usersRepo = g.get_repo(repostring[3] + "/" + repostring[4])
    except GithubException:
        send_error("This Repo Does not Exist",issue)
    
    master_ref = repo.get_git_ref('heads/main')
    base_tree = repo.get_git_tree(master_ref.object.sha)

    repos = repo.get_collaborators()
    
    if usersRepo.owner.id == issue.user.id:
        pass
    else:
        for r in repos:
            if r.id == issue.user.id:
                break
        send_error("You are not the creator of this repo",issue)

    data = file_checks(usersRepo,issue)

    if data['Info']['Type'] == "Stage":
        contents = repo.get_contents("stages/ml.beta.json")
        minified = json.loads(contents.decoded_content)

        try:
            repodic = {
                "folder-name": data["Stage"]["fileName"],
                "display-name": data["Stage"]["displayName"],
                "type": data['Info']['Type'],
                "tree": base_tree.sha,
                "version": data["Info"]["Version"],
                "id": usersRepo.id,
                "repository": repolink,
                "description":  data["Stage"]["description"],
                "author": data["Info"]["Creators"]
            }
        except Exception as ex:
            send_error("Your config.json file was missing crucial infomation",issue)

        minified["ssf2-mods"].append(repodic)
        mods_array = []
        for d in minified["ssf2-mods"]:
            mods_array.append([
                d["display-name"],
                d["author"],
                d["repository"],
                d["version"],
                d["description"]])

        writer = MarkdownTableWriter(
        table_name= "SSF2 Mod Center",
        headers=["Mod name", "Author", "Homepage", "Version", "Description"],
        value_matrix=mods_array,
        margin=1
        )
        #writer.write_table()

        #repo.update_file("stages/ml.beta.json","stage json updated", json.dumps(minified),contents.sha)

        mdcontents = repo.get_contents("stages/README.md")
        #repo.update_file("stages/README.md","stage read me updated", writer.dumps(),mdcontents.sha)


        master_ref = repo.get_git_ref('heads/main')
        base_tree = repo.get_git_tree(master_ref.object.sha)
        print(base_tree)

    #print(minified)




def file_checks(repo:Repository,issue):
    try:
        contents = repo.get_contents("src/config.json")
    except GithubException:
        send_error("[Error]: Could not find the config.json file",issue)
    content = contents.decoded_content

    try:
        minified = json.loads(contents.decoded_content)
    except JSONDecodeError:
        send_error("[Error]: Could not Parse Your config.json file",issue)
    
    return minified

    

def send_error(error:str,issue):
    print("error")
    issue.create_comment(error)
    sys.exit(0)




if __name__ == "__main__":
    main()