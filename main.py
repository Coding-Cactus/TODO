import flask, uuid, hashlib, os
from datetime import datetime
from easypydb import DB

dbtoken = os.getenv('dbTOKEN')

userDB = DB('userDB', dbtoken)
todoDB = DB('todoDB', dbtoken)


app = flask.Flask(__name__)
app.secret_key = os.getenv('secretKey')
session = flask.session
 
def hash_password(password):
	salt = uuid.uuid4().hex
	return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt
    
def check_password(hashed_password, user_password):
	password, salt = hashed_password.split(':')
	return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()
 

@app.route('/')
def main():
	colours = {}
	tasks = []
	completedTasks = False
	order = flask.request.args.get('order')
	if 'user' in session:
		orderTasks1 = []
		orderTasks2 = []
		for x in todoDB[session['user']]:
			orderTasks1.append(x)
		for a in range(len(orderTasks1)-1, -1, -1):
			orderTasks2.append(orderTasks1[a])
		for i in orderTasks1:
			if int(datetime.strptime(todoDB[session['user']][i]['deadline'],"%d %B %Y, %H:%M").timestamp()) < datetime.now().timestamp():
				colours[i] = '#520a2d'
			else:
				colours[i] = '#0a522d'
		for h in orderTasks1:
			if todoDB[session['user']][h]['complete'] == True:
				completedTasks = True
				colours[h] = '#2d0a52'
		if order != 'new':
			if order == 'old':
				for x in orderTasks1:
					tasks.append(x)
			else:
				db = todoDB[session['user']]
				times = []
				for x in db:
					times.append(db[x]['deadlineTime'])
				times.sort()
				for a in times:
					for s in db:
						if db[s]['deadlineTime'] == a and s not in tasks:
							tasks.append(s)
							break
		else:
			db = todoDB[session['user']]
			for x in orderTasks2:
				tasks.append(x)
	return flask.render_template('todo.html', session=session, todo=todoDB, colours=colours, tasks=tasks, completedTasks=completedTasks)

@app.route('/signup')
def getSignin():
	return flask.render_template('signup.html', error='')


@app.route('/signup', methods=['POST'])
def signup():
	username = flask.request.form['username']
	password1 = flask.request.form['password1']
	password2 = flask.request.form['password2']
	if username in userDB.data:
		return flask.render_template('signup.html', error='Already a user with that name.')
	elif len(password1) < 6:
		return flask.render_template('signup.html', error='Password needs to be at least 6 characters long')
	elif password1 != password2:
		return flask.render_template('signup.html', error='Passwords did not match')
	else:
		userDB[username] = hash_password(password1)
		session['user'] = username
		session.modified = True
		todoDB[username] = {}
		return flask.redirect('/')

@app.route('/login')
def getLogin():
	return flask.render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
	username = flask.request.form['username']
	password = flask.request.form['password']
	if username not in userDB.data:
		return flask.render_template('login.html', error='Incorrect username or password.')
	elif check_password(userDB[username], password):
		session['user'] = username
		session.modified = True
		return flask.redirect('/')
	else:
		return flask.render_template('login.html', error='Incorrect username or password.')

@app.route('/logout')
def logout():
	session.pop('user', None)
	return flask.redirect('/')


@app.route('/add')
def getAdd():
	if 'user' in session:
		return flask.render_template('add.html')
	else:
		return flask.redirect('/')

@app.route('/add', methods=['POST'])
def add():
	user = session['user']
	oldTtitle = flask.request.form['title']
	desc = flask.request.form['description']
	deadline = flask.request.form['deadline']
	title = oldTtitle
	for i in oldTtitle:
		if oldTtitle[-1] == ' ':
			title = oldTtitle[:-1]
			oldTtitle = oldTtitle[:-1]
		else:
			break
	if title == '':
		return flask.render_template('add.html', title=title, desc=desc, deadline=deadline, error='You didn\'t give a title!')
	if deadline == '':
		return flask.render_template('add.html', title=title, desc=desc, deadline=deadline, error='You didn\'t give a deadline!')
	deadline_time = int(datetime.strptime(deadline,"%d %B %Y, %H:%M").timestamp())
	if user not in todoDB.data:
		new = {}
	else:
		new = todoDB[user]
	if title.lower() in new:
		return flask.render_template('add.html', title=title, desc=desc, deadline=deadline, error='Already a task with that name!')
	else:
		new[title] = {
			'description':desc,
			'deadline':deadline,
			'deadlineTime':deadline_time,
			'complete':False
		}
		todoDB[user] = new
		return flask.redirect('/')


@app.route('/delete/<name>')
def delete(name):
	if 'user' not in session:
		return flask.redirect('/')
	else:
		user = session['user']
		new = todoDB[user]
		if name not in new:
			return flask.redirect('/')
		else:
			del new[name]
			todoDB[user] = new
			return flask.redirect('/')

@app.route('/complete/<name>')
def complete(name):
	if 'user' not in session:
		return flask.redirect('/')
	else:
		user = session['user']
		new = todoDB[user]
		if name not in new:
			return flask.redirect('/')
		else:
			new[name]['complete'] = not new[name]['complete']
			todoDB[user] = new
			return flask.redirect('/')

@app.route('/favicon.ico')
def fav():
	return flask.send_file('favicon.ico')

app.run('0.0.0.0')