from flask import Flask,render_template,flash,request,redirect, send_file,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required,logout_user,current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from processor import processor
from werkzeug.utils import secure_filename
import os



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///mydb.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY']='SUPERSECRETKEY'

UPLOAD_FOLDER = './static/process/'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
##############
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

login_manager = LoginManager(app)




class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username= db.Column(db.String(50),unique=True)
    password=db.Column(db.String(50),nullable=False)
    wallet= db.Column(db.Integer,default=0)
    hassubscription=db.Column(db.Boolean,default=0)


admin=Admin(app,name='ADMIN',template_mode='bootstrap3')
admin.add_view(ModelView(User,db.session))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('index.html')

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'POST' and request.form.get('username') and request.form.get('password'):
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            user = User.query.filter_by(username=username).first()
            if user.password == password:
                login_user(user)
                flash('YOU ARE NOW LOGGED IN')
                return render_template('login.html')
            else: 
                flash('wrong Password')
                return render_template('login.html')
        else:
            flash('USER DOES NOT EXIST')
            return render_template('login.html')

        flash('THIS IS A MESSAGE')
    return render_template('login.html')

def createuser(username,password):
    user = User(username=username,password=password)
    db.session.add(user)
    db.session.commit()




@app.route('/process/', methods=['POST', 'GET'])
@login_required
def process():
    f = request.files['file']
    if f.filename == '':
        return render_template('image.html', message='CHOOSE FILE')

    if f.filename.split('.')[1] in app.config['ALLOWED_EXTENSIONS']:
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        processor(f.filename)
        return redirect(url_for('downloadgate', filename=f.filename))
    else:
        return render_template('image.html', message='Not A IMG')

@app.route('/image')
@login_required
def image():
    return render_template('image.html', message='GREYSCALER')

@app.route('/downloadgate/<filename>')
@login_required
def downloadgate(filename):
    if current_user.hassubscription:
        return redirect(url_for('download', filename=filename))
    else:
        if int(current_user.wallet) > 15:
            message= ' 1 process costs 15 usd press download to continue'
            return render_template('downloadgate.html',filename=filename,message=message)
        else :
            return render_template('deposit.html')  

@app.route('/download/<filename>')
@login_required
def download(filename):
    if current_user.hassubscription:
        filelocation = './static/process/'+filename
        return send_file(filelocation, as_attachment=True)
    else:
        newwalletamount = int(current_user.wallet)-15
        print(newwalletamount)
        current_user.wallet = newwalletamount
        db.session.commit()
        filelocation = './static/process/'+filename
        return send_file(filelocation, as_attachment=True)




@app.route('/deposit',methods=['POST','GET'])
def deposit():
    return render_template('deposit.html')


@app.route('/deposit/success/',methods=['POST','GET'])
def depositsuccessfull():
    if request.get_json(silent=True).get('payment'):
        amount = request.get_json(silent=True).get('payment')
        newwalletamount = int(current_user.wallet) + int(amount)
        current_user.wallet = newwalletamount
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
