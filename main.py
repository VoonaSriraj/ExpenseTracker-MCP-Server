from fastmcp import FastMCP
import os
import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
BUDGETS_PATH = os.path.join(os.path.dirname(__file__), "budgets.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        # Main expenses table
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT '',
                payment_method TEXT DEFAULT '',
                location TEXT DEFAULT '',
                recurring_id INTEGER DEFAULT NULL,
                tags TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recurring expenses template table
        c.execute("""
            CREATE TABLE IF NOT EXISTS recurring_expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT '',
                frequency TEXT NOT NULL, -- daily, weekly, monthly, yearly
                next_due_date TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Income tracking table
        c.execute("""
            CREATE TABLE IF NOT EXISTS income(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source TEXT NOT NULL,
                category TEXT DEFAULT 'salary',
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

init_db()

# ============== BASIC EXPENSE OPERATIONS ==============

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note="", payment_method="", location="", tags=""):
    '''Add a new expense entry to the database with enhanced fields.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """INSERT INTO expenses(date, amount, category, subcategory, note, payment_method, location, tags) 
               VALUES (?,?,?,?,?,?,?,?)""",
            (date, amount, category, subcategory, note, payment_method, location, tags)
        )
        return {"status": "ok", "id": cur.lastrowid, "message": f"Added expense of ${amount} for {category}"}

@mcp.tool()
def update_expense(expense_id, date=None, amount=None, category=None, subcategory=None, 
                   note=None, payment_method=None, location=None, tags=None):
    '''Update an existing expense entry.'''
    with sqlite3.connect(DB_PATH) as c:
        # First check if expense exists
        existing = c.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        if not existing:
            return {"status": "error", "message": f"Expense with ID {expense_id} not found"}
        
        # Build update query dynamically
        updates = []
        params = []
        
        if date is not None:
            updates.append("date = ?")
            params.append(date)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if subcategory is not None:
            updates.append("subcategory = ?")
            params.append(subcategory)
        if note is not None:
            updates.append("note = ?")
            params.append(note)
        if payment_method is not None:
            updates.append("payment_method = ?")
            params.append(payment_method)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        
        if not updates:
            return {"status": "error", "message": "No fields to update"}
        
        params.append(expense_id)
        query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, params)
        
        return {"status": "ok", "message": f"Updated expense ID {expense_id}"}

@mcp.tool()
def delete_expense(expense_id):
    '''Delete an expense entry by ID.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cur.rowcount > 0:
            return {"status": "ok", "message": f"Deleted expense ID {expense_id}"}
        else:
            return {"status": "error", "message": f"Expense ID {expense_id} not found"}

@mcp.tool()
def list_expenses(start_date, end_date, category=None, payment_method=None, location=None, tag=None):
    '''List expense entries within date range with optional filters.'''
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT id, date, amount, category, subcategory, note, payment_method, location, tags
            FROM expenses
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        if payment_method:
            query += " AND payment_method = ?"
            params.append(payment_method)
        if location:
            query += " AND location LIKE ?"
            params.append(f"%{location}%")
        if tag:
            query += " AND tags LIKE ?"
            params.append(f"%{tag}%")
            
        query += " ORDER BY date DESC, id DESC"
        
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

# ============== INCOME TRACKING ==============

@mcp.tool()
def add_income(date, amount, source, category="salary", note=""):
    '''Add income entry to track earnings.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO income(date, amount, source, category, note) VALUES (?,?,?,?,?)",
            (date, amount, source, category, note)
        )
        return {"status": "ok", "id": cur.lastrowid, "message": f"Added income of ${amount} from {source}"}

@mcp.tool()
def list_income(start_date, end_date, source=None):
    '''List income entries within date range.'''
    with sqlite3.connect(DB_PATH) as c:
        query = "SELECT * FROM income WHERE date BETWEEN ? AND ?"
        params = [start_date, end_date]
        
        if source:
            query += " AND source LIKE ?"
            params.append(f"%{source}%")
            
        query += " ORDER BY date DESC"
        
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

# ============== RECURRING EXPENSES ==============

@mcp.tool()
def add_recurring_expense(name, amount, category, frequency, next_due_date, subcategory="", note=""):
    '''Add a recurring expense template (daily, weekly, monthly, yearly).'''
    valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
    if frequency not in valid_frequencies:
        return {"status": "error", "message": f"Frequency must be one of: {', '.join(valid_frequencies)}"}
    
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """INSERT INTO recurring_expenses(name, amount, category, subcategory, note, frequency, next_due_date) 
               VALUES (?,?,?,?,?,?,?)""",
            (name, amount, category, subcategory, note, frequency, next_due_date)
        )
        return {"status": "ok", "id": cur.lastrowid, "message": f"Added recurring expense: {name}"}

@mcp.tool()
def list_recurring_expenses(active_only=True):
    '''List all recurring expense templates.'''
    with sqlite3.connect(DB_PATH) as c:
        query = "SELECT * FROM recurring_expenses"
        if active_only:
            query += " WHERE active = 1"
        query += " ORDER BY next_due_date ASC"
        
        cur = c.execute(query)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def process_due_recurring_expenses(date=None):
    '''Process recurring expenses that are due and create actual expense entries.'''
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    with sqlite3.connect(DB_PATH) as c:
        # Find due recurring expenses
        due_expenses = c.execute(
            "SELECT * FROM recurring_expenses WHERE next_due_date <= ? AND active = 1",
            (date,)
        ).fetchall()
        
        processed = []
        for expense in due_expenses:
            expense_id, name, amount, category, subcategory, note, frequency, next_due_date, active, created_at = expense
            
            # Create the actual expense entry
            c.execute(
                """INSERT INTO expenses(date, amount, category, subcategory, note, recurring_id) 
                   VALUES (?,?,?,?,?,?)""",
                (date, amount, category, subcategory, f"[Recurring: {name}] {note}", expense_id)
            )
            
            # Calculate next due date
            next_date = datetime.strptime(next_due_date, "%Y-%m-%d")
            if frequency == 'daily':
                next_date += timedelta(days=1)
            elif frequency == 'weekly':
                next_date += timedelta(weeks=1)
            elif frequency == 'monthly':
                if next_date.month == 12:
                    next_date = next_date.replace(year=next_date.year + 1, month=1)
                else:
                    next_date = next_date.replace(month=next_date.month + 1)
            elif frequency == 'yearly':
                next_date = next_date.replace(year=next_date.year + 1)
            
            # Update next due date
            c.execute(
                "UPDATE recurring_expenses SET next_due_date = ? WHERE id = ?",
                (next_date.strftime("%Y-%m-%d"), expense_id)
            )
            
            processed.append({"name": name, "amount": amount, "category": category})
        
        return {"status": "ok", "processed": processed, "count": len(processed)}

# ============== ADVANCED ANALYTICS ==============

@mcp.tool()
def summarize(start_date, end_date, category=None, group_by="category"):
    '''Summarize expenses with flexible grouping options.'''
    valid_groups = ['category', 'subcategory', 'payment_method', 'location', 'month', 'day_of_week']
    if group_by not in valid_groups:
        return {"status": "error", "message": f"group_by must be one of: {', '.join(valid_groups)}"}
    
    with sqlite3.connect(DB_PATH) as c:
        if group_by == 'month':
            query = """
                SELECT strftime('%Y-%m', date) as period, SUM(amount) as total_amount, COUNT(*) as count
                FROM expenses WHERE date BETWEEN ? AND ?
            """
        elif group_by == 'day_of_week':
            query = """
                SELECT 
                    CASE strftime('%w', date)
                        WHEN '0' THEN 'Sunday'
                        WHEN '1' THEN 'Monday'
                        WHEN '2' THEN 'Tuesday'
                        WHEN '3' THEN 'Wednesday'
                        WHEN '4' THEN 'Thursday'
                        WHEN '5' THEN 'Friday'
                        WHEN '6' THEN 'Saturday'
                    END as period,
                    SUM(amount) as total_amount,
                    COUNT(*) as count
                FROM expenses WHERE date BETWEEN ? AND ?
            """
        else:
            query = f"""
                SELECT {group_by} as period, SUM(amount) as total_amount, COUNT(*) as count
                FROM expenses WHERE date BETWEEN ? AND ?
            """
        
        params = [start_date, end_date]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        if group_by in ['month', 'day_of_week']:
            query += " GROUP BY period ORDER BY total_amount DESC"
        else:
            query += f" GROUP BY {group_by} ORDER BY total_amount DESC"
        
        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def get_spending_trends(months=6):
    '''Analyze spending trends over the last N months.'''
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT 
                strftime('%Y-%m', date) as month,
                category,
                SUM(amount) as total_amount
            FROM expenses 
            WHERE date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', date), category
            ORDER BY month DESC, total_amount DESC
        """.format(months)
        
        cur = c.execute(query)
        results = cur.fetchall()
        
        # Organize by month
        trends = defaultdict(list)
        for month, category, amount in results:
            trends[month].append({"category": category, "amount": amount})
        
        return dict(trends)

@mcp.tool()
def get_expense_statistics(start_date, end_date):
    '''Get comprehensive statistics for expenses in date range.'''
    with sqlite3.connect(DB_PATH) as c:
        # Basic stats
        stats = c.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(amount) as total_spent,
                AVG(amount) as avg_transaction,
                MIN(amount) as min_transaction,
                MAX(amount) as max_transaction
            FROM expenses WHERE date BETWEEN ? AND ?
        """, (start_date, end_date)).fetchone()
        
        # Top categories
        top_categories = c.execute("""
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM expenses WHERE date BETWEEN ? AND ?
            GROUP BY category ORDER BY total DESC LIMIT 5
        """, (start_date, end_date)).fetchall()
        
        # Daily average
        days_count = c.execute("""
            SELECT COUNT(DISTINCT date) as days 
            FROM expenses WHERE date BETWEEN ? AND ?
        """, (start_date, end_date)).fetchone()[0]
        
        daily_avg = stats[1] / max(days_count, 1)  # Avoid division by zero
        
        return {
            "total_transactions": stats[0],
            "total_spent": stats[1],
            "average_transaction": stats[2],
            "min_transaction": stats[3],
            "max_transaction": stats[4],
            "daily_average": daily_avg,
            "days_tracked": days_count,
            "top_categories": [{"category": cat, "total": total, "count": count} 
                             for cat, total, count in top_categories]
        }

# ============== BUDGET MANAGEMENT ==============

@mcp.tool()
def set_budget(category, monthly_limit, start_date=None):
    '''Set or update budget limit for a category.'''
    if start_date is None:
        start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    
    try:
        with open(BUDGETS_PATH, 'r') as f:
            budgets = json.load(f)
    except FileNotFoundError:
        budgets = {}
    
    budgets[category] = {
        "monthly_limit": monthly_limit,
        "start_date": start_date
    }
    
    with open(BUDGETS_PATH, 'w') as f:
        json.dump(budgets, f, indent=2)
    
    return {"status": "ok", "message": f"Set budget for {category}: ${monthly_limit}/month"}

@mcp.tool()
def check_budget_status(month=None):
    '''Check current budget status for all categories.'''
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    
    try:
        with open(BUDGETS_PATH, 'r') as f:
            budgets = json.load(f)
    except FileNotFoundError:
        return {"status": "error", "message": "No budgets set"}
    
    start_date = f"{month}-01"
    # Get last day of month
    year, month_num = map(int, month.split('-'))
    last_day = calendar.monthrange(year, month_num)[1]
    end_date = f"{month}-{last_day:02d}"
    
    with sqlite3.connect(DB_PATH) as c:
        status = []
        for category, budget_info in budgets.items():
            spent = c.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE category = ? AND date BETWEEN ? AND ?",
                (category, start_date, end_date)
            ).fetchone()[0]
            
            limit = budget_info['monthly_limit']
            remaining = limit - spent
            percent_used = (spent / limit) * 100 if limit > 0 else 0
            
            status.append({
                "category": category,
                "budget_limit": limit,
                "spent": spent,
                "remaining": remaining,
                "percent_used": percent_used,
                "over_budget": spent > limit
            })
        
        return {"month": month, "budget_status": status}

# ============== SEARCH AND FILTERING ==============

@mcp.tool()
def search_expenses(query, start_date=None, end_date=None):
    '''Search expenses by note, category, subcategory, location, or tags.'''
    with sqlite3.connect(DB_PATH) as c:
        sql_query = """
            SELECT id, date, amount, category, subcategory, note, payment_method, location, tags
            FROM expenses WHERE (
                note LIKE ? OR 
                category LIKE ? OR 
                subcategory LIKE ? OR 
                location LIKE ? OR 
                tags LIKE ?
            )
        """
        params = [f"%{query}%"] * 5
        
        if start_date:
            sql_query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            sql_query += " AND date <= ?"
            params.append(end_date)
        
        sql_query += " ORDER BY date DESC"
        
        cur = c.execute(sql_query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def get_expense_by_id(expense_id):
    '''Get detailed information about a specific expense.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
        row = cur.fetchone()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        else:
            return {"status": "error", "message": f"Expense ID {expense_id} not found"}

# ============== DATA EXPORT/IMPORT ==============

@mcp.tool()
def export_expenses_csv(start_date, end_date, filename=None):
    '''Export expenses to CSV format.'''
    if filename is None:
        filename = f"expenses_{start_date}_to_{end_date}.csv"
    
    with sqlite3.connect(DB_PATH) as c:
        expenses = c.execute("""
            SELECT date, amount, category, subcategory, note, payment_method, location, tags
            FROM expenses WHERE date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (start_date, end_date)).fetchall()
    
    # Create CSV content
    csv_content = "Date,Amount,Category,Subcategory,Note,Payment Method,Location,Tags\n"
    for expense in expenses:
        # Escape commas in text fields
        row = [str(field).replace(',', ';') if field else '' for field in expense]
        csv_content += ",".join(row) + "\n"
    
    return {
        "status": "ok",
        "filename": filename,
        "content": csv_content,
        "record_count": len(expenses)
    }

# ============== FINANCIAL HEALTH ==============

@mcp.tool()
def calculate_net_worth(month=None):
    '''Calculate net worth (income - expenses) for a given month.'''
    if month is None:
        month = datetime.now().strftime("%Y-%m")
    
    start_date = f"{month}-01"
    year, month_num = map(int, month.split('-'))
    last_day = calendar.monthrange(year, month_num)[1]
    end_date = f"{month}-{last_day:02d}"
    
    with sqlite3.connect(DB_PATH) as c:
        total_income = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()[0]
        
        total_expenses = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date BETWEEN ? AND ?",
            (start_date, end_date)
        ).fetchone()[0]
        
        net_worth = total_income - total_expenses
        savings_rate = (net_worth / total_income * 100) if total_income > 0 else 0
        
        return {
            "month": month,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_worth": net_worth,
            "savings_rate": savings_rate
        }

# ============== RESOURCES ==============

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    '''Read expense categories configuration.'''
    try:
        with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Return default categories if file doesn't exist
        default_categories = {
            "categories": [
                "Food & Dining", "Transportation", "Shopping", "Entertainment",
                "Bills & Utilities", "Healthcare", "Travel", "Education",
                "Personal Care", "Home", "Miscellaneous"
            ],
            "payment_methods": [
                "Cash", "Credit Card", "Debit Card", "Bank Transfer",
                "Digital Wallet", "Check"
            ]
        }
        return json.dumps(default_categories, indent=2)

@mcp.resource("expense://budgets", mime_type="application/json")
def budgets():
    '''Read budget configuration.'''
    try:
        with open(BUDGETS_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({}, indent=2)

if __name__ == "__main__":
    mcp.run()