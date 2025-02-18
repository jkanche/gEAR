#!/opt/bin/python3

"""
Loads user question/comment and any new 'tags' into the database

"""

import cgi
import json
import os, sys

lib_path = os.path.abspath(os.path.join('..', '..', 'lib'))
sys.path.append(lib_path)
import geardb

def main():
    print('Content-Type: application/json\n\n')

    result = {'success':0}

    cnx = geardb.Connection()
    cursor = cnx.get_cursor()

    form = cgi.FieldStorage()
#    session_id = form.getvalue('session_id')
#    user_id = get_user_id_from_session_id(cursor, session_id)

    firstname = form.getvalue('submitter_firstname')
    lastname = form.getvalue('submitter_lastname')
    email = form.getvalue('submitter_email')
    title = form.getvalue('comment_title')
    comment = form.getvalue('comment')
    tag = form.getvalue('comment_tag')
    print(tag, file=sys.stderr)
    security_check = form.getvalue('super_impressive_security_check')

    is_read = 0 # 0 = not read (false)

    ## Insert the comment information
    add_comment_sql = """
        INSERT INTO comment (first_name, last_name, email, title, message, is_read, date_added)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """
    cursor.execute(add_comment_sql, (firstname, lastname, email, title, comment, is_read))
    comment_id = cursor.lastrowid

    # Insert any Tags
    if tag is not None:
        tag_list = []
        raw_tags = tag.split(', ')
        print(raw_tags, file=sys.stderr)

        # Ensures duplicates are removed
        for tag in raw_tags:
            if tag not in tag_list:
                tag_list.append(tag)

        print(tag_list, file=sys.stderr)

        #Get list of tags already in gEAR
        qry_get_tags = """
            SELECT label, id
            FROM tag
        """
        cached_tags = {}
        cursor.execute(qry_get_tags)
        for row in cursor:
            cached_tags[row[0].lower()] = row[1]

        add_tag_sql = """
            INSERT INTO tag (label)
            VALUES (%s)
        """
        add_commenttag_sql = """
            INSERT INTO comment_tag (tag_id, comment_id)
            VALUES (%s, %s)
        """
        for tag in tag_list:
            #Check if new tag is already in database
            if tag.lower() not in cached_tags:
                #New tag. Add it to database and keep its id
                cursor.execute(add_tag_sql, (tag,))
                cnx.commit()
                tag_id = cursor.lastrowid
            else:
                #Tag exists. Get its id
                tag_id = cached_tags[tag.lower()]

            cursor.execute(add_commenttag_sql, (tag_id, comment_id,) )
            cnx.commit()


    cnx.commit()
    cursor.close()
    cnx.close()

    result['success'] = 1
    print(json.dumps(result))



def get_user_id_from_session_id(cursor, session_id):
    qry = ( "SELECT user_id FROM user_session WHERE session_id = %s" )
    cursor.execute(qry, (session_id, ) )
    user_id = None

    for (uid,) in cursor:
        user_id = uid

    return user_id


if __name__ == '__main__':
    main()
