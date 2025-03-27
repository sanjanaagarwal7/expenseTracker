from application import app, db
from flask import render_template, url_for, redirect, flash, request, jsonify
from application.form import UserDataForm
from application.models import IncomeExpenses
import json
import google.generativeai as genai
genai.configure(api_key="AIzaSyDWJGxRm79vJivcNFtCkMMyA0e3169MyB4")
@app.route('/')
def index():
    entries = IncomeExpenses.query.order_by(IncomeExpenses.date.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/add', methods=["POST", "GET"])
def add_expense():
    form = UserDataForm()
    if form.validate_on_submit():
        entry = IncomeExpenses(type=form.type.data, category=form.category.data, amount=form.amount.data)
        db.session.add(entry)
        db.session.commit()
        flash(f"{form.type.data} has been added to {form.type.data}s", "success")
        return redirect(url_for('index'))
    return render_template('add.html', title="Add expenses", form=form)

@app.route('/delete-post/<int:entry_id>')
def delete(entry_id):
    entry = IncomeExpenses.query.get_or_404(int(entry_id))
    db.session.delete(entry)
    db.session.commit()
    flash("Entry deleted", "success")
    return redirect(url_for("index"))



@app.route('/dashboard')
def dashboard():
    income_vs_expense = db.session.query(db.func.sum(IncomeExpenses.amount), IncomeExpenses.type).group_by(IncomeExpenses.type).order_by(IncomeExpenses.type).all()
    category_comparison = db.session.query(db.func.sum(IncomeExpenses.amount), IncomeExpenses.category).group_by(IncomeExpenses.category).order_by(IncomeExpenses.category).all()
    dates = db.session.query(db.func.sum(IncomeExpenses.amount), IncomeExpenses.date).group_by(IncomeExpenses.date).order_by(IncomeExpenses.date).all()

    return render_template('dashboard.html',
                            income_vs_expense=json.dumps([x[0] for x in income_vs_expense]),
                            income_category=json.dumps([x[0] for x in category_comparison]),
                            over_time_expenditure=json.dumps([x[0] for x in dates]),
                            dates_label=json.dumps([x[1].strftime("%m-%d-%y") for x in dates]))

@app.route('/gemini_insights', methods=['POST'])
def gemini_insights():
    try:
        data = IncomeExpenses.query.all()
        expenses = [f"{entry.category}: {entry.amount}" for entry in data]
        prompt = f"Analyze these expenses and provide savings tips: {', '.join(expenses)}"

        model = genai.GenerativeModel("gemini-1.5-pro-001")
        response = model.generate_content(prompt)

        return jsonify({"insights": response.text if response else "No insights available."})
    except Exception as e:
        return jsonify({"insights": "Error fetching insights"}), 500