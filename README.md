# ExpenseTracker MCP Server

A comprehensive expense tracking and financial management MCP (Model Context Protocol) server built with FastMCP. Track expenses, manage budgets, analyze spending patterns, and monitor your financial health with advanced analytics capabilities.

## Features

### Core Expense Management
- Add, update, and delete expenses with detailed categorization
- Support for subcategories, payment methods, locations, and tags
- Date-based filtering and advanced search functionality
- Comprehensive expense lookup and modification tools

### Income Tracking
- Track income from multiple sources with categorization
- Monitor earnings patterns and trends over time
- Support for various income types and sources

### Recurring Expenses
- Set up recurring expense templates with flexible frequencies (daily, weekly, monthly, yearly)
- Automatic processing of due recurring expenses
- Template management and tracking system

### Advanced Analytics
- Flexible expense summarization with multiple grouping options
- Multi-month spending trend analysis
- Comprehensive financial statistics and reporting
- Budget tracking with overspending alerts

### Financial Health Tools
- Net worth calculation and monitoring
- Savings rate analysis
- Budget management with compliance tracking
- Data export capabilities for external analysis

## Prerequisites

- Python 3.8 or higher
- FastMCP library
- Claude Desktop or MCP-compatible client

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/VoonaSriraj/expense-tracker-mcp.git
```

### 2. Install Dependencies

```bash
pip install fastmcp
```

### 3. Create Configuration Files

Create a `categories.json` file in the project directory:

```json
{
  "categories": [
    "Food & Dining",
    "Transportation", 
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Travel",
    "Education",
    "Personal Care",
    "Home",
    "Miscellaneous"
  ],
  "payment_methods": [
    "Cash",
    "Credit Card", 
    "Debit Card",
    "Bank Transfer",
    "Digital Wallet",
    "Check"
  ]
}
```

### 4. Run the MCP Server

```bash
uv run fastmcp install claude-desktop run main.py
```

## This Configuration will be automatically added after excuting above command

### Claude Desktop Integration

Add the server to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "python",
      "args": ["/absolute/path/to/expense_tracker.py"],
      "env": {}
    }
  }
}
```

### Alternative Configuration (using uv)

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": ["run", "/absolute/path/to/expense_tracker.py"],
      "env": {}
    }
  }
}
```

## Usage Guide

### Basic Expense Operations

#### Adding Expenses

```python
# Simple expense entry
add_expense("2024-01-15", 25.50, "Food & Dining", "Lunch", "Business lunch")

# Detailed expense with all fields
add_expense(
    date="2024-01-15",
    amount=25.50, 
    category="Food & Dining",
    subcategory="Lunch",
    note="Business lunch with client",
    payment_method="Credit Card",
    location="Downtown Cafe",
    tags="business,tax-deductible"
)
```

#### Managing Existing Expenses

```python
# List expenses for a date range
list_expenses("2024-01-01", "2024-01-31")

# Update an existing expense
update_expense(expense_id=1, amount=30.00, note="Updated lunch cost")

# Delete an expense
delete_expense(expense_id=1)

# Search expenses by keyword
search_expenses("coffee")
```

### Income Management

```python
# Add income entry
add_income("2024-01-31", 5000, "Salary", "salary", "Monthly salary payment")

# List income for a specific period
list_income("2024-01-01", "2024-01-31")

# Filter income by source
list_income("2024-01-01", "2024-01-31", source="Freelance")
```

### Recurring Expenses

```python
# Set up monthly subscription
add_recurring_expense(
    name="Netflix Subscription",
    amount=15.99,
    category="Entertainment", 
    frequency="monthly",
    next_due_date="2024-02-01"
)

# Process all due recurring expenses
process_due_recurring_expenses()

# View all recurring expense templates
list_recurring_expenses()
```

### Budget Management

```python
# Set monthly budget limits
set_budget("Food & Dining", 500)
set_budget("Transportation", 200)

# Check current budget status
check_budget_status("2024-01")
```

### Analytics and Reporting

```python
# Generate expense summary by category
summarize("2024-01-01", "2024-01-31", group_by="category")

# Analyze spending trends over multiple months
get_spending_trends(months=6)

# Get comprehensive expense statistics
get_expense_statistics("2024-01-01", "2024-01-31")

# Calculate monthly net worth
calculate_net_worth("2024-01")
```

### Data Export

```python
# Export expenses to CSV format
export_expenses_csv("2024-01-01", "2024-01-31", "january_expenses.csv")
```

## Database Schema

The server automatically creates and manages SQLite database tables:

### Tables

- **expenses**: Primary expense records with detailed attributes
- **recurring_expenses**: Templates for automated recurring expenses  
- **income**: Income tracking and categorization

### Key Fields

**Expenses Table:**
- Basic: id, date, amount, category, subcategory, note
- Extended: payment_method, location, tags, recurring_id, created_at

**Income Table:**
- Fields: id, date, amount, source, category, note, created_at

**Recurring Expenses Table:**
- Fields: id, name, amount, category, frequency, next_due_date, active

## File Structure

```
expense-tracker-mcp/
├── expense_tracker.py      # Main MCP server implementation
├── expenses.db            # SQLite database (auto-generated)
├── categories.json        # Expense categories configuration
├── budgets.json          # Budget settings (auto-generated)
├── README.md             # Documentation
└── LICENSE               # License file
```

## Available MCP Tools

### Expense Management Tools
- `add_expense` - Create new expense entries with detailed attributes
- `update_expense` - Modify existing expense records  
- `delete_expense` - Remove expense entries from database
- `list_expenses` - Retrieve expenses with filtering options
- `get_expense_by_id` - Get detailed information for specific expense
- `search_expenses` - Search expenses across all text fields

### Income Management Tools
- `add_income` - Record income entries with source tracking
- `list_income` - Retrieve income records with filtering

### Recurring Expense Tools
- `add_recurring_expense` - Create recurring expense templates
- `list_recurring_expenses` - View all recurring expense templates
- `process_due_recurring_expenses` - Process and create due recurring expenses

### Analytics Tools
- `summarize` - Generate expense summaries with flexible grouping
- `get_spending_trends` - Analyze spending patterns over time
- `get_expense_statistics` - Calculate comprehensive financial statistics

### Budget Management Tools
- `set_budget` - Configure monthly budget limits by category
- `check_budget_status` - Monitor budget compliance and spending

### Financial Analysis Tools
- `calculate_net_worth` - Compute net worth and savings rates

### Data Export Tools
- `export_expenses_csv` - Export expense data in CSV format

## Available MCP Resources

- `expense://categories` - Access expense categories and payment methods configuration
- `expense://budgets` - Access current budget settings and limits

## Development

### Project Structure

The codebase is organized into logical sections:
- Database initialization and schema management
- Core CRUD operations for expenses and income
- Recurring expense automation
- Advanced analytics and reporting
- Budget management system
- Search and filtering capabilities
- Data export functionality

### Extending the Server

To add new functionality:

1. Define new database tables in the `init_db()` function if needed
2. Create new tool functions using the `@mcp.tool()` decorator
3. Add appropriate error handling and validation
4. Update the documentation accordingly

## API Documentation

### Tool Parameters

Most tools accept standard parameters:
- **Date formats**: YYYY-MM-DD (ISO 8601)
- **Amount formats**: Decimal numbers (e.g., 25.50)
- **Optional parameters**: Use empty strings or None for optional fields

### Error Handling

All tools return structured responses:
```python
{
    "status": "ok|error",
    "message": "Description of result or error",
    "data": {}  # Additional data when applicable
}
```

## Contributing

### Guidelines

1. Fork the repository and create a feature branch
2. Follow existing code style and patterns
3. Add appropriate error handling and validation
4. Update documentation for new features
5. Write clear commit messages
6. Submit a pull request with detailed description

### Code Style

- Use descriptive variable and function names
- Include docstrings for all public functions
- Handle database connections properly with context managers
- Validate input parameters before processing
- Return consistent response formats

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support and Issues

### Getting Help

- Review the documentation and examples above
- Check existing GitHub issues for similar problems
- Create a new issue with detailed information including:
  - Python version and operating system
  - Error messages and stack traces
  - Steps to reproduce the issue
  - Expected vs actual behavior

### Known Limitations

- Single-user local database (SQLite)
- No built-in data backup functionality
- Limited to local file system storage
- No real-time synchronization capabilities

## Roadmap

### Planned Features

- Multi-currency support with exchange rates
- Receipt image attachment and OCR processing
- Investment portfolio tracking
- Advanced tax reporting and categorization
- REST API interface for third-party integrations
- Data backup and synchronization options
- Enhanced reporting with charts and graphs

### Performance Improvements

- Database indexing optimization
- Query performance enhancements
- Memory usage optimization for large datasets
- Batch processing capabilities for bulk operations# ExpenseTracker-MCP-Server
