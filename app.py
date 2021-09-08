from flask import Flask, render_template, url_for, request, redirect, g, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, desc   
from datetime import datetime
from functools import wraps
import re

#---------------------------------------------------------------------------------------------------------------------------------------
#datascience packages --> create requirements.txt
import pandas as pd
import matplotlib as plt
import numpy as np
import json
import requests
from sqlalchemy.sql.elements import Null
from yahooquery import Ticker, ticker
import time, sched

#app configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.secret_key = 'somesecretkeythatonlyishouldknow'

#---------------------------------------------------------------------------------------------------------------------------------------
#NOTES:
#implement credential storage
#homepage w/ user detail -> breadcrumbs, navbar etc
#sessions
#use postgresql or something else
#prevent app crashes via blocking functions/ try catch

#---------------------------------------------------------------------------------------------------------------------------------------
#defining the user class
class User:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User: {self.username}>'


#approved user list
#do not keep admin/ admin as the creds -> look into storing and hashing creds on sqlite etc
users = []
users.append(User(id=1, username='admin', password='admin'))

@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']][0]
        g.user = user


#login page -> only page visible to internet
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)

        username = request.form['username']
        password = request.form['password']
        
        user = [x for x in users if x.username == username][0]
        if user and user.password == password:
            session['user_id'] = user.id
            return redirect(url_for('index'))
 
        return redirect(url_for('login'))

    return render_template('login.html')


#backend authenticator - https://flask.palletsprojects.com/en/1.0.x/patterns/viewdecorators/
def login_required(status=None):
    def login_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'user_id' in session and (status is None or status in session):
                return func(*args, **kwargs)
            else:
                return redirect("/login")
        return wrapper
    return login_decorator

#---------------------------------------------------------------------------------------------------------------------------------------
#Database Models, note, delete the database before adding more columns
# import db from app
# db.create_all()
class Import(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_col = db.Column(db.String(200))
    date_created2 = db.Column(db.String(200))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

class Hist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    cost = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return '<Task %r>' % self.id

class savings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    def __repr__(self):
        return '<Task %r>' % self.id

class Ticker1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(200))
    quantity = db.Column(db.String(200))
    price = db.Column(db.String(200))

class TickHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(200))
    quantity = db.Column(db.String(200))
    price = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Networth(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(200))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    credit = db.Column(db.String(200))
    info = db.Column(db.String(200))
    total = db.Column(db.String(200))
    
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    debit = db.Column(db.String(200))
    info = db.Column(db.String(200))
    total = db.Column(db.String(200))

    #def __init__(self, id, ticker, quantity, price):
     #  self.id = id
     #  self.ticker = ticker

#---------------------------------------------------------------------------------------------------------------------------------------
@app.route
@app.route('/home', methods=['POST', 'GET'])
#Requirements: Wealth Summary, Split, Monthly Expenses, Change via week, account page reroute
def home():
    return render_template('home.html')

#index and task post function
@app.route('/index', methods=['POST', 'GET'])
@login_required()
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        cost_content = request.form['content2']
        income_content = request.form['content3']
        
        new_task = Todo(content=task_content, cost=cost_content)
        history = Hist(content=task_content, cost=cost_content)
        savinginput = savings(cost=cost_content)
        
        #look into issue with adding integers to sqlite3 and redo below
        #expenseinput
        expensedb = Expense.query.all()
        expensedb2 = expensedb[-1].total
        expensedb3 = float(expensedb2)
        formexpense = float(cost_content)
        total = expensedb3 + formexpense
        total2 = str(total)
        expenseinput = Expense(credit=cost_content, total=total, info=task_content)

        #incomeinput
        incomedb = Income.query.all()
        incomedb2 = incomedb[-1].total
        incomedb3 = float(incomedb2)
        formincome = float(income_content)
        total3 = incomedb3 + formincome
        total4 = str(total3)
        incomeinput = Income(debit=income_content, total=total4, info=task_content)

        #networthinput
        nwdb = Networth.query.all()
        nwdb2  = nwdb[-1].value
        nwdb3 = float(nwdb2)
        nwdb4 = nwdb3 + (formincome - formexpense)
        nwdb5 = str(nwdb4)
        nwinput = Networth(value=nwdb5)

        try:
            db.session.add(new_task)
            db.session.add(history)
            db.session.add(savinginput)
            db.session.add(expenseinput)
            db.session.add(incomeinput)
            db.session.add(nwinput)
            db.session.commit()
            
            return redirect('/index')
        except:
            return 'There was an issue adding your task'
    
    else:
        sum2 = db.session.query(db.func.sum(Todo.cost)).all()
        sum1 = str(sum2)

        for char in '[](),':
            sum1 = sum1.replace(char,'')

        result = db.session.query(Todo.date_created).order_by(Todo.date_created.desc()).first()
        saving = db.session.query(savings.date_created).order_by(savings.date_created.desc()).first()
    
        if not result or not saving:
            tasks = Todo.query.order_by(Todo.date_created).all()
            return render_template('index.html', tasks=tasks)
        
        else:
            #there is an issue, adding a new expense updates the cost of that expense to the db, overwriting the expense limit...
            #ceiling = db.session.query(savings.cost).last()
            ceiling = savings.query.all()
            ceiling2 = str(ceiling[-1].cost)
            ceiling3 = float(ceiling2)

            sum3 = float(sum1)
            #remainder = ceiling2
            #ceiling = int(400)
                #maxexp = request.form['maxexp2']
                #maxexp2 = int(maxexp)
                #remainder = maxexp2 - sum3
            tasks = Todo.query.order_by(Todo.date_created).all()
            remainder = ceiling3 - sum3
            if ceiling3 > sum3:
                response = "Good"
            else:
                response = "Bad"

            return render_template('index.html', tasks=tasks, ceiling=ceiling3, sum1=sum1, remainder=remainder, response=response)


@app.route('/importsaving', methods=['POST', 'GET'])
@login_required()
def importsave():
    if request.method == 'POST':
        saving = request.form['maxexp2']
        new_task = savings(cost=saving)

        try:
            db.session.add(new_task)
            db.session.commit()
            
            return redirect('/index')
        except:
            return 'There was an issue adding your task'
    else:
        return render_template('importsaving.html')


#import expenses for the paycycle
#the below is an example of how to add a button and keep u on the same page, i.e. post and not move
@app.route('/import', methods=['GET', 'POST'])
def import_expense():
    sum8 = db.session.query(db.func.sum(Todo.cost)).all()
    sum4 = str(sum8)
    for char in '[](),':
        sum20 = sum4.replace(char,'')

    default_time = datetime.now()
    default_time_string = str(default_time)
    totalexpense = Import(expense_col=sum20, date_created2=default_time_string)
    db.session.add(totalexpense)
    db.session.commit()
    return redirect('/index')


#delete task function
@app.route('/index/<int:id>')
@login_required()
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/index')
    except:
        return 'There was a problem deleting that task'


#update task function and page
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required()
def update(id):
    tasks = Todo.query.get_or_404(id)

    if request.method == 'POST':
        tasks.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/index')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('update.html', tasks=tasks)


#delete all function
#a function is executed once the page is loaded, redirect to index once run
@app.route("/delete", methods=['GET', 'POST'])
@login_required()
def deleteall():
    #test1 = data["currentPrice"]
    db.session.query(Todo).delete()
    db.session.commit()
    return redirect('/index')

#finance projector
#grab the imported expenses
#as soon as a new expense is added, import the newest expense
#sum of expenses for a time period/ paycycle
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    salary = db.Column(db.String(200), nullable=False)
    period = db.Column(db.String(200))
    currentworth = db.Column(db.String(200))
    fixedexpenses = db.Column(db.String(200))
    projectiontf = db.Column(db.String(200))
    date_created3 = db.Column(db.DateTime, default=datetime.utcnow)

#----------------------------------------------------------------------------------------------------------------------------------------
#FINANCIAL TRACKER
#----------------------------------------------------------------------------------------------------------------------------------------
#API
@app.route("/stockdata", methods=['GET'])
@login_required()
#the below is a test of the yahoofinance api
def api2():
    #add the db query to where 'pltr' is....
    pltr = Ticker('pltr')
    #aapl = Ticker('aapl')
    data  = pltr.financial_data
    data2 = data['pltr']['currentPrice']
    data3 = data2
    qty = 3
    total = data3 * qty
    pltr= "PLTR"
    #test1 = data["currentPrice"]
    
    return render_template('portfolio.html', data=data3, qty=qty, totalstock=total, pltr=pltr)
    #time.sleep(60.0 - ((time.time() - starttime) % 60))
#run the app + server


@app.route('/stocktest', methods=['POST', 'GET'])

def addstock():
    if request.method == 'POST':
        stockreq = request.form['stock1']
        todb = Ticker1(ticker=stockreq)

        try:
            db.session.add(todb)
            db.session.commit()
            return redirect('/stocktest')
        except:
            return redirect('/stocktest')


    stock = Ticker1.query.all()
    stock2 = str(stock[-1].ticker)

    #return render
    return render_template('stocktest.html', stock=stock2)

@app.route('/networth', methods=['POST', 'GET'])
def nw():
    return render_template('networth.html')

#----------------------------------------------------------------------------------------------------------------------
#Stock Manager + Dividends
@app.route('/stocktrack', methods=['POST', 'GET'])
@login_required()
#Notes: There is an issue; if you add a same stock it will not update the quantity, but add a new stock
def stocktrack():
    if request.method == 'POST':
        ticker_content = request.form['content']
        quant_content = request.form['content2']

        list = ["start"]
        for row in Ticker1.query:
            x = row.ticker
            list.append(x)
            print(list)

        if ticker_content not in list:
            price2 = stockcalc(ticker_content)
            price1 = str(price2)
            new_task = Ticker1(ticker=ticker_content, quantity=quant_content, price=price1)
            print(price1)
            stk = Ticker(ticker_content)
            stk2 = stk.financial_data
            stk3 = stk2[ticker_content]['currentPrice']
            stk4 = float(quant_content) * stk3

            nwdb = Networth.query.all()
            nwdb2  = nwdb[-1].value
            nwdb3 = float(nwdb2)
            nwdb4 = nwdb3 + stk4
            nwdb5 = str(nwdb4)

            stockinput = Networth(value=nwdb5)

            try:
                db.session.add(new_task)
                db.session.add(stockinput)
                db.session.commit()
                
                return redirect('/stocktrack')
            except:
                return 'There was an issue adding your task'
        
        else:
            for row4 in Ticker1.query.filter_by(ticker=ticker_content):
                qty = int(row4.quantity)
                qty2 = int(quant_content)
                qty3 = qty + qty2
                qty4 = str(qty3)
                row4.quantity = qty4
                print(row4.ticker)
                db.session.commit()
            return redirect('/stocktrack')

    else:       
        for row in Ticker1.query:
            data = Ticker(row.ticker)
            data2 = data.financial_data
            data3 = data2[row.ticker]['currentPrice']
            data4 = data3 * int(row.quantity)
            #print(Ticker1.query.filter_by(id=row.id))
            for update in Ticker1.query.filter_by(id=row.id):
                update.price = data4
                db.session.commit()

        db.session.commit()

        stocksum = db.session.query(db.func.sum(Ticker1.price)).all()
        stocksumstr = str(stocksum)
        
        forma = stocksumstr.strip("[](),")
        forma2 = str(forma)

        #tickers = Ticker('fb', asynchronous=True)
        #df = tickers.history()
        #result = df.head()
        #result2 = result.to_html()

        tasks1 = Ticker1.query.order_by(Ticker1.ticker).all()
        return render_template('stocktrack.html', tasks1=tasks1, forma2=forma2)
    

def stockcalc(y):
    calc = Ticker(y)
    data = calc.financial_data
    data2 = data[y]['currentPrice']
    return(data2)

@app.route('/stocktest2')
def test():
    #for row in Ticker1.query:
    #    if 'AAPL' in row.ticker:
    #        print('yes')
    #    else:
    #       print('no')
    
    # = 'AAPL'
    #if 'AAPL' in Ticker1.query.ticker():
    #    print('yes')
    list = ["start"]
    for row in Ticker1.query:
        x = row.ticker
        list.append(x)
    print(list)
    #test
    if 'TSLA' in list:
        print('yes')
    else:
        print('no')

    return redirect('/stocktrack')


@app.route('/stocktrack/<int:id>')
@login_required()
def delete1(id):
    task_to_delete = Ticker1.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/stocktrack')
    except:
        return 'There was a problem deleting that task'


@app.route('/stockupdate/<int:id>', methods=['GET', 'POST'])
@login_required()
def updateStock(id):
    tasks = Ticker1.query.get_or_404(id)

    if request.method == 'POST':
        tasks.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/stocktrack')
        except:
            return 'There was an issue updating your task'

    else:
        return render_template('stockupdate.html', tasks=tasks)


#---------------------------------------------------------------------------------------------------------------------------------------
#run the app
if __name__ == "__main__":
    app.run(debug=True)


