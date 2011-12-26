from flask import render_template
import MySQLdb
from flask import Flask,request,session
import flask
import database as db
from datetime import datetime
import hashlib
app = Flask(__name__)

conn = None
conn = MySQLdb.connect('localhost','root','','oc')
cur = conn.cursor()
def isLoggedIn():
    return  'username' in session

def initSession(id,name):
    session['user_id'] = id
    session['username'] = name
def login():
    return flask.redirect(flask.url_for('signup'))
def globals():
    return {'username':session['username'],'user_id':session['user_id']}

@app.route('/')
def index():
    if not isLoggedIn():
        return login()
    g = globals()

    return render_template('index.html',**g)

@app.route('/about')
def about():
    if not isLoggedIn():
        return login()
    g = globals()

    return render_template('about.html',**g)

@app.route('/categories')
def categories():
    if not isLoggedIn():
        return login()

    res = cur.execute('select name,image from category order by cat_id asc') 
    categories = []
    for c in cur.fetchall():
        cat = c[0]
        sanitized = cat.lower().replace(' ','+')
        categories.append({'url':sanitized,'image':c[1]})
    
    g = globals()
    g.update({'categories':categories,'tab':'categories'})

    return render_template('categories.html',**g)

@app.route('/category/<category>')
def category(category):
    if not isLoggedIn():
        return login()

    # fetch the category id from the name
    category = category.replace('+',' ')
    cur.execute('select cat_id from category where name=%s', (category,))
    cat_id = cur.fetchone()[0]

    # fetch the discussions for this category
    res = cur.execute('select d_id,user.name,title,postDate,content from discussion inner join user using (user_id) where cat_id=%s',(cat_id,))
    posts = []
    cur2 = conn.cursor()
    for discussion in cur.fetchall():
        tags = db.fetchDiscussionTags(cur2,discussion[0])
        posts.append({'id':discussion[0], 'title':discussion[2],  \
                      'user':discussion[1], \
                      'date': discussion[3], \
                      'tags': tags})
    popular_tags = db.fetchPopularTags(cur,cat_id)

    g = globals()
    g.update({'popular':popular_tags,'posts':posts,'category_name':category,'category_url':category.replace(' ','+')})


    return render_template('category.html',**g)
@app.route('/discussion/<id>')
def discussion(id):
    if not isLoggedIn():
        return login()

    # fetch the main discussion metadata
    res = cur.execute('select user.name,title,postDate,content,cat_id from (discussion inner join user using (user_id)) where d_id=%s',(id,))
    discussion = cur.fetchone()
    cur.execute('select name from category where cat_id=%s',(discussion[4],))
    categoryName = cur.fetchone()[0]
    tags = db.fetchDiscussionTags(cur,id)
    popular_tags = db.fetchPopularTags(cur,discussion[4])

    # populate the data object 
    discussion = {'id': id, 'title':discussion[1], \
                  'user':discussion[0], \
                   'date': discussion[2], \
                   'content': discussion[3], \
                   'tags': tags, \
                  }
    responses = db.fetchResponses(cur,id)

    g = globals()
    g.update({'discussion':discussion,'popular':popular_tags,'responses':responses,'category_name':categoryName,'category_url':categoryName.replace(' ','+')})


    return render_template('discussion.html',**g)
@app.route('/post',methods=['POST'])
def post():
    print 'post'

@app.route('/reply',methods=['POST'])
def reply():
    if not isLoggedIn():
        return login()
    d_id = request.form['d_id']
    data = request.form['data']

    cur.execute('insert into response (d_id,user_id,replyDate,content) values (%s,%s,NOW(),%s)',(d_id,session['user_id'],data))
    conn.commit()

    return "true"

@app.route('/signup',methods=['GET','POST'])
def signup():
    # don't let the user sign up if he's logged in
    if isLoggedIn():
        return flask.redirect(flask.url_for('index'))

    # display the page?
    if request.method == 'GET':
        return render_template('signup.html')

    # process the form submission
    res = cur.execute('insert into user (name,email,password) values (%s,%s,%s)', (request.form['username'],request.form['email'],hashlib.sha224(request.form['password']).hexdigest()))
    conn.commit()
    initSession(cur.lastrowid,request.form['username'])
    
    return index()
    
@app.route('/logout')
def logout():
    session.pop('username',None)
    session.pop('user_id',None)
    return flask.redirect(flask.url_for('signup'))

@app.route('/trending')
def trending():
    if not isLoggedIn():
        return login()
    d = db.fetchTrendingDiscussions(cur)

    g = globals()
    g.update({'entries':d})
    return render_template('trending.html',**g)

app.debug = True
app.secret_key = 'hello, how are you today?'
app.run()
