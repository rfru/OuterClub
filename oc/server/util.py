import re
import cgi
import smtplib
import datetime
from email.mime.text import MIMEText

qtext = '[^\\x0d\\x22\\x5c\\x80-\\xff]'
dtext = '[^\\x0d\\x5b-\\x5d\\x80-\\xff]'
atom = '[^\\x00-\\x20\\x22\\x28\\x29\\x2c\\x2e\\x3a-\\x3c\\x3e\\x40\\x5b-\\x5d\\x7f-\\xff]+'
quoted_pair = '\\x5c[\\x00-\\x7f]'
domain_literal = "\\x5b(?:%s|%s)*\\x5d" % (dtext, quoted_pair)
quoted_string = "\\x22(?:%s|%s)*\\x22" % (qtext, quoted_pair)
domain_ref = atom
sub_domain = "(?:%s|%s)" % (domain_ref, domain_literal)
word = "(?:%s|%s)" % (atom, quoted_string)
domain = "%s(?:\\x2e%s)*" % (sub_domain, sub_domain)
local_part = "%s(?:\\x2e%s)*" % (word, word)
addr_spec = "%s\\x40%s" % (local_part, domain)

emailValidator = re.compile('\A%s\Z' % addr_spec)
def emailValid(s):
    return emailValidator.match(s)

def formatCategoryName(c):
    return ' '.join([spl.capitalize() if len(spl) > 2 else spl.upper() for spl in c.split(' ')])

def escape(s):
    return cgi.escape(s)

MENTION_REGEX = re.compile(r'(^|\W)(@\w+)',flags=re.MULTILINE)
def replaceMentions(cur,data):
    users = findMentions(cur,data)
    isAction = data.startswith('/me')
    
    accum = ''
    matches = MENTION_REGEX.finditer(data)
    end = None
    for m in matches:
        accum += data[:m.start()]
        name = m.group(2)
        if (len(name) > 1):
            accum += m.group(1)
            name = name[1:]
            lname = name.lower()
            if lname in users and users[lname] != None:
                u = users[lname] 
                
                if isAction:
                    accum += '<a class="mention" href="#!/user/%s"><img width="30" height="30" src="/static/images/avatars/%s" /></a>' % (u['user_id'],u['avatar_image'])
                else:
                    accum += '<a class="mention" href="#!/user/%s">@%s</a>' % (u['user_id'],name)
            else:
                accum += m.group()
        else:
            accum += m.group()
        end = m.end()
    if (end):
        accum += data[end:]
    else:
        accum = data
    return accum

def findMentions(cur,data):
    mentions = MENTION_REGEX.finditer(data)

    users = dict()
    mentionsSet = set()
    for m in mentions:
        name = m.group(2).lower().strip()
        if (len(name) > 1):
            mentionsSet.add(name[1:])
    if (len(mentionsSet) > 0):
        replacements = map(lambda x:'%s',mentionsSet)
        cur.execute('select name,user_id,avatar_image from user where LCASE(name) in (%s)' % ','.join(replacements),tuple(mentionsSet))
        for u in cur.fetchall():
            users[u[0].lower()] = {'user_id':u[1],'avatar_image':u[2]}
        for n in mentionsSet:
            if not (n in users):
                users[n] = None
    
    return users

class Upvote:
    UserType = 0

def send(config,to,subject,msg):
    m = MIMEText(msg,'html')
    fro = '"OuterClub" <%s>' % config['EMAIL_ADDRESS']
    m['From'] = fro
    m['To'] = to
    m['Subject'] = subject
    server = smtplib.SMTP_SSL(config['EMAIL_SERVER'],config['EMAIL_PORT'])
    server.login(config['EMAIL_USER'],config['EMAIL_PASSWORD'])
    server.sendmail(fro,to,m.as_string())
    server.quit()

