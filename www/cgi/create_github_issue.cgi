#!/opt/bin/python3

"""
Creates a Github issue from a submitted comment on the gEAR page.

"""

import cgi, json, os, requests, sys
from dotenv import load_dotenv
from requests.exceptions import HTTPError
from pathlib import Path

env_path = Path('..') / '.env'  # .env file is in "www" directory
load_dotenv(dotenv_path=env_path)


GITHUB_ACCESS_TOKEN=os.getenv("GITHUB_ACCESS_TOKEN")
GEAR_GIT_URL="https://api.github.com/repos/jorvis/gEAR/issues"
ASSIGNEES=["echrysostomou84"]

SITE_COMMENTS_PROJ_URL="https://api.github.com/projects/columns/8150789/cards"

def main():

    print('Content-Type: application/json\n\n')
    result = {'error': [], 'success': 0 }

    form = cgi.FieldStorage()
    firstname = form.getvalue('submitter_firstname')
    lastname = form.getvalue('submitter_lastname')
    email = form.getvalue('submitter_email')
    title = form.getvalue('comment_title')
    comment = form.getvalue('comment')
    tag = form.getvalue('comment_tag')

    if not tag:
        tag = ''

    # In an effort to not blow up the "tags" field in github, I will just indicate the tags in the body of the Github issue
    body = (f"**From:** {firstname} {lastname}\n\n"
           f"**Email:** {email}\n\n"
           f"**Msg:** {comment}\n\n"
           f"**Tags:** {tag.split(', ')}")

    # Headers data (i.e. authentication)
    headers = { "Authorization": "token {}".format(GITHUB_ACCESS_TOKEN) }

    # Issue metadata
    data = {
        "title":title,
        "body":body,
        "labels":["site_comment"],
        "assignees":ASSIGNEES
    }

    # Code from https://realpython.com/python-requests/
    try:
        response = requests.post(GEAR_GIT_URL, data = json.dumps(data), headers = headers)

        # If the response was successful (200- and 300- level status codes), no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        result["error"] = f'HTTP error occurred: {http_err}'
    except Exception as err:
        result["error"] = f'Other error occurred: {err}'
    else:
        result["success"] = 1
    print(json.dumps(result))

    # Add to 'Site comments' projects board
    headers["Accept"] = 'application/vnd.github.inertia-preview+json'
    content_id = response.json()["id"]   # ID of ticket just created
    data = {
        "content_id": content_id,
        "content_type": "Issue"
    }
    try:
        response = requests.post(SITE_COMMENTS_PROJ_URL, data = json.dumps(data), headers = headers )
        # If the response was successful (200- and 300- level status codes), no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print("HTTP error occurred{}.\n Count not assign id {} to 'Site Comments' project card".format(http_err, content_id), file=sys.stderr)
    except Exception as err:
        print("Other error occurred{}.\n Count not assign id {} to 'Site Comments' project card".format(err, content_id), file=sys.stderr)



if __name__ == '__main__':
    main()
