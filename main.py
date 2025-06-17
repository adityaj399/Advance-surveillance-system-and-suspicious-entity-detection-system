# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response,jsonify
from werkzeug import secure_filename
import sqlite3
import pandas as pd
from datetime import datetime
import os
from human2 import *
from firebaseUpload import *

name = ''
patrolling_mode = False
num_soldiers = 0

app = Flask(__name__)

app.secret_key = '1234'
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	global name
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
		try:
			name = cursorObj.fetchone()[0]
			return redirect(url_for('video'))
		except:
			error = "Invalid Credentials Please try again..!!!"
			return render_template('login.html',error=error)
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		if request.form['sub']=='Submit':
			name = request.form['name']
			email = request.form['email']
			password = request.form['password']
			rpassword = request.form['rpassword']
			pet = request.form['pet']
			if(password != rpassword):
				error='Password dose not match..!!!'
				return render_template('register.html',error=error)
			try:
				con = sqlite3.connect('mydatabase.db')
				cursorObj = con.cursor()
				cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
			
				if(cursorObj.fetchone()):
					error = "User already Registered...!!!"
					return render_template('register.html',error=error)
			except:
				pass
			now = datetime.now()
			dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
			con = sqlite3.connect('mydatabase.db')
			cursorObj = con.cursor()
			cursorObj.execute("CREATE TABLE IF NOT EXISTS Users (Date text,Name text,Email text,password text,pet text)")
			cursorObj.execute("INSERT INTO Users VALUES(?,?,?,?,?)",(dt_string,name,email,password,pet))
			con.commit()

			return redirect(url_for('login'))

	return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
	error = None
	global name
	if request.method == 'POST':
		email = request.form['email']
		pet = request.form['pet']
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT password from Users WHERE Email='{email}' AND pet = '{pet}';")
		
		try:
			password = cursorObj.fetchone()
			#print(password)
			error = "Your password : "+password[0]
		except:
			error = "Invalid information Please try again..!!!"
		return render_template('forgot-password.html',error=error)
	return render_template('forgot-password.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
	global name
	return render_template('home.html',name=name)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
	level,paper,plastic,metal,glass,biodegradable,cardboard = readFirebase()
	return render_template('dashboard.html',name=name,level=level,paper=paper,plastic=plastic,metal=metal,
	glass=glass,biodegradable=biodegradable,cardboard=cardboard)


'''
@app.route('/image', methods=['GET', 'POST'])
def image():
	if request.method=='POST':
		savepath = r'static/img/'
		f = request.files['doc']
		f.save(os.path.join(savepath,(secure_filename('test.jpg'))))
		return redirect(url_for('image_test'))
	return render_template('image.html',name=name)

@app.route('/image_test', methods=['GET', 'POST'])
def image_test():
	gtype = ''
	result,index = predict()
	parameter = parameters()
	if(index == 1 or index == 3 or index == 4 or index == 7 or index == 9):
		gtype = 'Organic'
		now = datetime.now()
		dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS Result (Date text,Garbage text,Type text,Weight text,Hydrogen text,Fertilizer text)")
		cursorObj.execute("INSERT INTO Result VALUES(?,?,?,?,?,?)",(dt_string,result,gtype,parameter[0],parameter[1],parameter[2]))
		con.commit()
		sendSMS("Garbage:" + str(parameter[0]) + ", Type:organic" + ", Weight:" + str(parameter[1]) + ", Hydrogen:"
		+str(parameter[1]) + ", Fertilizer:"+str(parameter[2]))
		return render_template('image_test.html',name=name,
		result=result,weight=parameter[0],hydrogen=parameter[1],fertilizer=parameter[2],gtype=gtype)
	else:
		gtype = 'Harmful'
		now = datetime.now()
		dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute("CREATE TABLE IF NOT EXISTS Result (Date text,Garbage text,Type text,Weight text,Hydrogen text,Fertilizer text)")
		cursorObj.execute("INSERT INTO Result VALUES(?,?,?,?,?,?)",(dt_string,result,gtype,parameter[0],"-","-"))
		con.commit()
		sendSMS("Garbage:"+str(parameter[0])+", Type:Harmful"+", Weight:"+str(parameter[1])+", Hydrogen:"
		+"-" + ", Fertilizer:"+"-")
		return render_template('image_test.html',name=name,
		result=result,weight=parameter[0],gtype=gtype)
	return render_template('image_test.html')

@app.route('/record', methods=['GET', 'POST'])
def view_feedbackfeedback():
	global name
	conn = sqlite3.connect('mydatabase.db', isolation_level=None,
						detect_types=sqlite3.PARSE_COLNAMES)
	df = pd.read_sql_query(f"SELECT * from Result;", conn)
	
	return render_template('record.html',name=name,tables=[df.to_html(classes='table-responsive table table-bordered table-hover')], titles=df.columns.values)
'''
@app.route('/update_patrolling_mode', methods=['POST'])
def update_patrolling_mode():
	global patrolling_mode, num_soldiers
	data = request.get_json()
	patrolling_mode = data.get('patrolling', False)  # Get the patrolling mode state
	num_soldiers = data.get('num_soldiers', 0)  # Default to 0 if not provided
	print(num_soldiers)
	file_path = 'mode.txt'
	with open(file_path, 'w') as file:
		file.write(str(patrolling_mode)+","+str(num_soldiers))

	print(f"Patrolling Mode: {'On' if patrolling_mode else 'Off'}")
	# Return response
	return jsonify({
		"message": "Patrolling mode and number of soldiers updated successfully",
		"patrolling": patrolling_mode,
		"num_soldiers": num_soldiers
	})

@app.route('/video', methods=['GET', 'POST'])
def video():
	global name
	return render_template('video.html',name=name)

@app.route('/video_stream')
def video_stream():
	global name,patrolling_mode
	return Response(video_feed(name),mimetype='multipart/x-mixed-replace; boundary=frame')

# No caching at all for API endpoints.
@app.after_request
def add_header(response):
	# response.cache_control.no_store = True
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response


if __name__ == '__main__' and run:
	app.run(host='0.0.0.0', debug=False, threaded=True)
