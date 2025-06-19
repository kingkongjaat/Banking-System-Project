import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import uuid
from abc import ABC, abstractmethod
import datetime
from typing import Optional

# =======================
# DATA MODEL CLASSES
# =======================

class Account(ABC):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0):
        self._account_number = account_number
        self._account_holder_id = account_holder_id
        self._balance = initial_balance

    @property
    def account_number(self):
        return self._account_number

    @property
    def balance(self):
        return self._balance

    @property
    def account_holder_id(self):
        return self._account_holder_id

    @abstractmethod
    def deposit(self, amount: float) -> bool:
        pass

    @abstractmethod
    def withdraw(self, amount: float) -> bool:
        pass

    def display_details(self) -> str:
        return f"Acc No: {self._account_number}, Balance: Rs. {self._balance:.2f}"

    @abstractmethod
    def to_dict(self) -> dict:
        return {
            "account_number": self._account_number,
            "balance": self._balance,
            "account_holder_id": self._account_holder_id
        }

class SavingsAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0, interest_rate: float = 0.01):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._interest_rate = interest_rate if interest_rate >= 0 else 0.01

    @property
    def interest_rate(self):
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value):
        if value >= 0:
            self._interest_rate = value

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or amount > self._balance:
            return False
        self._balance -= amount
        return True

    def apply_interest(self) -> None:
        interest = self._balance * self._interest_rate
        self._balance += interest

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Interest Rate: {self._interest_rate*100:.2f}%"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"type": "savings", "interest_rate": self._interest_rate})
        return base

class CurrentAccount(Account):
    def __init__(self, account_number: str, account_holder_id: str, initial_balance: float = 0.0, overdraft_limit: float = 0.0):
        super().__init__(account_number, account_holder_id, initial_balance)
        self._overdraft_limit = overdraft_limit if overdraft_limit >= 0 else 0.0

    @property
    def overdraft_limit(self):
        return self._overdraft_limit

    @overdraft_limit.setter
    def overdraft_limit(self, value):
        if value >= 0:
            self._overdraft_limit = value

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or (self._balance - amount) < (-1 * self._overdraft_limit):
            return False
        self._balance -= amount
        return True

    def display_details(self) -> str:
        base = super().display_details()
        return f"{base}, Overdraft Limit: Rs. {self._overdraft_limit:.2f}"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"type": "current", "overdraft_limit": self._overdraft_limit})
        return base

class Customer:
    def __init__(self, customer_id: str, name: str, address: str):
        self._customer_id = customer_id
        self._name = name
        self._address = address
        self._account_numbers = []

    @property
    def customer_id(self):
        return self._customer_id

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        self._address = value

    @property
    def account_numbers(self):
        return self._account_numbers.copy()

    def add_account_number(self, account_number: str) -> None:
        if account_number not in self._account_numbers:
            self._account_numbers.append(account_number)

    def remove_account_number(self, account_number: str) -> None:
        if account_number in self._account_numbers:
            self._account_numbers.remove(account_number)

    def display_details(self) -> str:
        return f"ID: {self._customer_id}\nName: {self._name}\nAddress: {self._address}\nAccounts: {len(self._account_numbers)}"

    def to_dict(self) -> dict:
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "address": self._address,
            "account_numbers": self._account_numbers
        }

class Bank:
    def __init__(self, customer_file='customers.json', account_file='accounts.json'):
        self._customers = {}
        self._accounts = {}
        self._customer_file = customer_file
        self._account_file = account_file
        self._load_data()
        self._transaction_history = []  # list of dicts to track transactions

    def _load_data(self):
        try:
            with open(self._customer_file, 'r', encoding='utf-8') as f:
                customers_data = json.load(f)
            for cdata in customers_data:
                c = Customer(cdata['customer_id'], cdata['name'], cdata['address'])
                for acc_num in cdata.get('account_numbers', []):
                    c.add_account_number(acc_num)
                self._customers[c.customer_id] = c
        except FileNotFoundError:
            self._customers = {}
        try:
            with open(self._account_file, 'r', encoding='utf-8') as f:
                accounts_data = json.load(f)
            for adata in accounts_data:
                acc_type = adata.get('type', None)
                if acc_type == 'savings':
                    acc = SavingsAccount(adata['account_number'], adata['account_holder_id'], adata.get('balance', 0.0), adata.get('interest_rate', 0.01))
                elif acc_type == 'current':
                    acc = CurrentAccount(adata['account_number'], adata['account_holder_id'], adata.get('balance', 0.0), adata.get('overdraft_limit', 0.0))
                else:
                    continue
                self._accounts[acc.account_number] = acc
        except FileNotFoundError:
            self._accounts = {}
        for c in self._customers.values():
            valid_accounts = [acc for acc in c.account_numbers if acc in self._accounts]
            c._account_numbers = valid_accounts

    def _save_data(self):
        customers_data = [c.to_dict() for c in self._customers.values()]
        accounts_data = [a.to_dict() for a in self._accounts.values()]
        with open(self._customer_file, 'w', encoding='utf-8') as f:
            json.dump(customers_data, f, indent=4)
        with open(self._account_file, 'w', encoding='utf-8') as f:
            json.dump(accounts_data, f, indent=4)
        with open("transactions.json", 'w', encoding='utf-8') as f:
            json.dump(self._transaction_history, f, indent=4)

    def add_customer(self, customer: Customer) -> bool:
        if customer.customer_id in self._customers:
            return False
        if len(customer.customer_id) != 9 or not customer.customer_id.isdigit():
            return False
        self._customers[customer.customer_id] = customer
        self._save_data()
        return True

    def remove_customer(self, customer_id: str) -> bool:
        cust = self._customers.get(customer_id)
        if not cust:
            return False
        if cust.account_numbers:
            return False
        del self._customers[customer_id]
        self._save_data()
        return True

    def create_account(self, customer_id: str, account_type: str, initial_balance: float = 0.0, **kwargs) -> Optional[Account]:
        customer = self._customers.get(customer_id)
        if not customer:
            return None
        account_number = str(uuid.uuid4())[:8]
        if account_type == 'savings':
            interest_rate = kwargs.get('interest_rate', 0.01)
            account = SavingsAccount(account_number, customer_id, initial_balance, interest_rate)
        elif account_type == 'current':
            overdraft_limit = kwargs.get('overdraft_limit', 0.0)
            account = CurrentAccount(account_number, customer_id, initial_balance, overdraft_limit)
        else:
            return None
        self._accounts[account_number] = account
        customer.add_account_number(account_number)
        self._save_data()
        return account

    def deposit(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if not account:
            return False
        success = account.deposit(amount)
        if success:
            self._transaction_history.append({
                "type": "deposit",
                "account": account_number,
                "amount": amount,
                "timestamp": datetime.datetime.now().isoformat()
            })
            self._save_data()
        return success

    def withdraw(self, account_number: str, amount: float) -> bool:
        account = self._accounts.get(account_number)
        if not account:
            return False
        success = account.withdraw(amount)
        if success:
            self._transaction_history.append({
                "type": "withdraw",
                "account": account_number,
                "amount": amount,
                "timestamp": datetime.datetime.now().isoformat()
            })
            self._save_data()
        return success

    def transfer_funds(self, from_acc_num: str, to_acc_num: str, amount: float) -> bool:
        from_account = self._accounts.get(from_acc_num)
        to_account = self._accounts.get(to_acc_num)
        if not from_account or not to_account:
            return False
        if amount <= 0:
            return False
        if not from_account.withdraw(amount):
            return False
        if not to_account.deposit(amount):
            from_account.deposit(amount)
            return False
        self._transaction_history.append({
            "type": "transfer",
            "from_account": from_acc_num,
            "to_account": to_acc_num,
            "amount": amount,
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save_data()
        return True

    def get_customer_accounts(self, customer_id: str) -> list:
        customer = self._customers.get(customer_id)
        if not customer:
            return []
        accounts = [self._accounts[acc_num] for acc_num in customer.account_numbers if acc_num in self._accounts]
        return accounts

    def apply_all_interest(self):
        for account in self._accounts.values():
            if isinstance(account, SavingsAccount):
                account.apply_interest()
        self._transaction_history.append({
            "type": "apply_interest",
            "timestamp": datetime.datetime.now().isoformat()
        })
        self._save_data()

    def get_transaction_history(self):
        return self._transaction_history

###########################
# GUI Classes
###########################

class BaseView(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
    def refresh_style(self):
        pass

class HomeView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        tk.Label(self, text="Welcome to Student Banking System", font=("Segoe UI", 24, "bold"), fg="#2563eb").pack(pady=40)
        tk.Label(self, text="Use the sidebar to navigate customer and account management, perform transactions,\napply interest, and view reports.", font=("Segoe UI", 12), justify=tk.CENTER).pack()

class CustomerManagementView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        frm_top = tk.Frame(self)
        frm_top.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(frm_top, text="Add Customer", command=self.add_customer).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="Remove Customer", command=self.remove_customer).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="Refresh List", command=self.populate_customers).pack(side=tk.LEFT, padx=4)

        columns = ("ID", "Name", "Address", "Accounts")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.populate_customers()

    def populate_customers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for c in self.app.bank._customers.values():
            self.tree.insert("", tk.END, iid=c.customer_id, values=(c.customer_id, c.name, c.address, len(c.account_numbers)))

    def add_customer(self):
        dlg = CustomerDialog(self, "Add New Customer")
        self.wait_window(dlg.top)
        if not dlg.result:
            return
        cust_id, name, addr = dlg.result
        if len(cust_id) != 9 or not cust_id.isdigit():
            messagebox.showerror("Invalid ID", "Customer ID must be exactly 9 digits numeric.")
            return
        if cust_id in self.app.bank._customers:
            messagebox.showerror("Exists", "Customer ID already exists.")
            return
        new_cust = Customer(cust_id, name, addr)
        if self.app.bank.add_customer(new_cust):
            self.populate_customers()
            self.app._set_status(f"Customer '{name}' added.")

    def remove_customer(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Remove Customer", "Select a customer first")
            return
        cust_id = selected[0]
        if self.app.bank.remove_customer(cust_id):
            self.populate_customers()
            self.app._set_status(f"Customer {cust_id} removed.")
        else:
            messagebox.showerror("Cannot Remove", "Customer has active accounts or does not exist.")

class CustomerDialog:
    def __init__(self, parent, title):
        top = self.top = tk.Toplevel(parent)
        top.title(title)
        top.grab_set()
        top.resizable(False, False)
        self.result = None

        tk.Label(top, text="Customer ID (9 digits):").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.entry_id = ttk.Entry(top)
        self.entry_id.grid(row=0, column=1, padx=8, pady=8)
        tk.Label(top, text="Name:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.entry_name = ttk.Entry(top)
        self.entry_name.grid(row=1, column=1, padx=8, pady=8)
        tk.Label(top, text="Address:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        self.entry_address = ttk.Entry(top)
        self.entry_address.grid(row=2, column=1, padx=8, pady=8)
        ttk.Button(top, text="OK", command=self.on_ok).grid(row=3, column=0, columnspan=2, pady=10)
        self.entry_id.focus()

    def on_ok(self):
        cid = self.entry_id.get().strip()
        name = self.entry_name.get().strip()
        addr = self.entry_address.get().strip()
        if not (cid and name and addr):
            messagebox.showerror("Invalid input", "All fields required.")
            return
        if len(cid) != 9 or not cid.isdigit():
            messagebox.showerror("Invalid ID", "Customer ID must be exactly 9 digits numeric.")
            return
        self.result = (cid, name, addr)
        self.top.destroy()

class AccountManagementView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        frm_top = tk.Frame(self)
        frm_top.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(frm_top, text="Create Account", command=self.create_account_dialog).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="Refresh List", command=self.populate_accounts).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="Delete Account", command=self.delete_account).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_top, text="Deposit", command=self.deposit_dialog).pack(side=tk.RIGHT, padx=4)
        ttk.Button(frm_top, text="Withdraw", command=self.withdraw_dialog).pack(side=tk.RIGHT, padx=4)

        columns = ("Account No", "Type", "Holder ID", "Balance", "Interest/Overdraft")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            width = 120 if col != "Balance" else 110
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.populate_accounts()

    def populate_accounts(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for a in self.app.bank._accounts.values():
            atype = "Savings" if isinstance(a, SavingsAccount) else "Current"
            iod = f"{a.interest_rate*100:.2f}%" if isinstance(a, SavingsAccount) else f"Rs. {a.overdraft_limit:.2f}"
            self.tree.insert("", tk.END, iid=a.account_number,
                             values=(a.account_number, atype, a.account_holder_id, f"Rs. {a.balance:.2f}", iod))

    def create_account_dialog(self):
        dlg = CreateAccountDialog(self, "Create New Account", self.app.bank)
        self.wait_window(dlg.top)
        if not dlg.result:
            return
        cust_id, acc_type, init_bal, spec_val = dlg.result
        kwargs = {}
        if acc_type == 'savings':
            kwargs['interest_rate'] = spec_val
        else:
            kwargs['overdraft_limit'] = spec_val
        account = self.app.bank.create_account(cust_id, acc_type, init_bal, **kwargs)
        if account:
            self.populate_accounts()
            self.app._set_status(f"{acc_type.title()} account created for customer {cust_id}.")
        else:
            messagebox.showerror("Failure", "Invalid customer ID or data.")

    def delete_account(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Delete Account", "Select an account first")
            return
        acc_no = selected[0]
        acc = self.app.bank._accounts.get(acc_no)
        if not acc:
            messagebox.showerror("Invalid selection", "Account does not exist")
            return
        cust = self.app.bank._customers.get(acc.account_holder_id)
        if cust:
            cust.remove_account_number(acc_no)
        del self.app.bank._accounts[acc_no]
        self.app.bank._save_data()
        self.populate_accounts()
        self.app._set_status(f"Account {acc_no} deleted.")

    def deposit_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Deposit", "Select an account first")
            return
        acc_no = selected[0]
        val = simpledialog.askfloat("Deposit", "Enter amount to deposit:")
        if val is None or val <= 0:
            return
        if self.app.bank.deposit(acc_no, val):
            messagebox.showinfo("Success", f"Deposited Rs. {val:.2f} in account {acc_no}")
            self.populate_accounts()
            self.app._set_status(f"Deposited Rs. {val:.2f} in account {acc_no}")
        else:
            messagebox.showerror("Error", "Deposit failed.")

    def withdraw_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Withdraw", "Select an account first")
            return
        acc_no = selected[0]
        val = simpledialog.askfloat("Withdraw", "Enter amount to withdraw:")
        if val is None or val <= 0:
            return
        if self.app.bank.withdraw(acc_no, val):
            messagebox.showinfo("Success", f"Withdrew Rs. {val:.2f} from account {acc_no}")
            self.populate_accounts()
            self.app._set_status(f"Withdrew Rs. {val:.2f} from account {acc_no}")
        else:
            messagebox.showerror("Error", "Withdrawal failed.")


class CreateAccountDialog:
    def __init__(self, parent, title, bank: Bank):
        top = self.top = tk.Toplevel(parent)
        top.title(title)
        top.grab_set()
        top.resizable(False, False)
        self.bank = bank
        self.result = None

        tk.Label(top, text="Customer ID (9 digits):").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.entry_cust = ttk.Combobox(top, values=list(self.bank._customers.keys()))
        self.entry_cust.grid(row=0, column=1, padx=8, pady=8)
        if self.entry_cust['values']:
            self.entry_cust.current(0)

        tk.Label(top, text="Account Type:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.acc_type = tk.StringVar(value="savings")
        ttk.Radiobutton(top, text="Savings", variable=self.acc_type, value="savings", command=self.update_special_label).grid(row=1, column=1, sticky="w", padx=2)
        ttk.Radiobutton(top, text="Current", variable=self.acc_type, value="current", command=self.update_special_label).grid(row=1, column=1, sticky="e", padx=2)

        tk.Label(top, text="Initial Balance (Rs):").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        self.entry_init = ttk.Entry(top)
        self.entry_init.grid(row=2, column=1, padx=8, pady=8)
        self.entry_init.insert(0, "0.00")

        self.spec_label = tk.Label(top, text="Interest Rate (%):")
        self.spec_label.grid(row=3, column=0, sticky="e", padx=8, pady=8)
        self.entry_spec = ttk.Entry(top)
        self.entry_spec.grid(row=3, column=1, padx=8, pady=8)
        self.entry_spec.insert(0, "1.00")

        ttk.Button(top, text="Create", command=self.on_create).grid(row=4, column=0, columnspan=2, pady=12)

    def update_special_label(self):
        if self.acc_type.get() == "savings":
            self.spec_label.config(text="Interest Rate (%):")
            self.entry_spec.delete(0, tk.END)
            self.entry_spec.insert(0, "1.00")
        else:
            self.spec_label.config(text="Overdraft Limit (Rs):")
            self.entry_spec.delete(0, tk.END)
            self.entry_spec.insert(0, "0.00")

    def on_create(self):
        cust_id = self.entry_cust.get().strip()
        acc_type = self.acc_type.get()
        try:
            init_bal = float(self.entry_init.get())
            if init_bal < 0:
                raise ValueError()
        except:
            messagebox.showerror("Invalid", "Invalid initial balance")
            return
        try:
            spec_val = float(self.entry_spec.get())
            if spec_val < 0:
                raise ValueError()
        except:
            messagebox.showerror("Invalid", "Invalid interest rate or overdraft")
            return
        if len(cust_id) != 9 or not cust_id.isdigit():
            messagebox.showerror("Invalid", "Customer ID must be exactly 9 digits")
            return
        self.result = (cust_id, acc_type, init_bal, spec_val)
        self.top.destroy()

class TransferFundsView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        frm = tk.Frame(self)
        frm.pack(pady=20, padx=20)

        tk.Label(frm, text="From Account Number:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky='e', pady=5)
        self.entry_from = ttk.Entry(frm)
        self.entry_from.grid(row=0, column=1, pady=5, padx=10)

        tk.Label(frm, text="To Account Number:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky='e', pady=5)
        self.entry_to = ttk.Entry(frm)
        self.entry_to.grid(row=1, column=1, pady=5, padx=10)

        tk.Label(frm, text="Amount (Rs):", font=("Segoe UI", 12)).grid(row=2, column=0, sticky='e', pady=5)
        self.entry_amount = ttk.Entry(frm)
        self.entry_amount.grid(row=2, column=1, pady=5, padx=10)

        ttk.Button(frm, text="Transfer", command=self.transfer).grid(row=3, column=0, columnspan=2, pady=15)

    def transfer(self):
        from_acc = self.entry_from.get().strip()
        to_acc = self.entry_to.get().strip()
        try:
            amount = float(self.entry_amount.get())
            if amount <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Error", "Enter positive numeric amount")
            return
        if not from_acc or not to_acc:
            messagebox.showerror("Error", "Both accounts required")
            return
        success = self.app.bank.transfer_funds(from_acc, to_acc, amount)
        if success:
            messagebox.showinfo("Success", f"Transferred Rs. {amount:.2f} from {from_acc} to {to_acc}")
            self.app._set_status(f"Transferred Rs. {amount:.2f} from {from_acc} to {to_acc}")
        else:
            messagebox.showerror("Failure", "Transfer failed; check account numbers and balances.")

class ApplyInterestView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        tk.Label(self, text="Apply Interest to All Savings Accounts", font=("Segoe UI", 16, "bold")).pack(pady=20)
        ttk.Button(self, text="Apply Interest Now", command=self.apply_interest).pack(pady=20)
        self.status_label = tk.Label(self, text="", font=("Segoe UI", 12))
        self.status_label.pack()

    def apply_interest(self):
        self.app.bank.apply_all_interest()
        self.status_label.config(text="Interest applied to all savings accounts.")
        self.app._set_status("Interest applied to savings accounts.")

class ReportView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.tree = None
        self._create_widgets()
        self.populate_reports()

    def _create_widgets(self):
        columns = ("Type", "Details", "Timestamp")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=200)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        ttk.Button(self, text="Refresh Reports", command=self.populate_reports).pack(pady=10)

    def populate_reports(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for record in self.app.bank.get_transaction_history():
            rtype = record.get('type', '')
            details = ''
            if rtype == 'deposit':
                details = f"Deposit Rs.{record.get('amount', 0):.2f} to {record.get('account','')}"
            elif rtype == 'withdraw':
                details = f"Withdraw Rs.{record.get('amount', 0):.2f} from {record.get('account','')}"
            elif rtype == 'transfer':
                details = f"Rs.{record.get('amount', 0):.2f} from {record.get('from_account','')} to {record.get('to_account','')}"
            elif rtype == 'apply_interest':
                details = "Applied Interest to all savings accounts"
            timestamp = record.get('timestamp', '')
            self.tree.insert('', tk.END, values=(rtype.title(), details, timestamp))

# ---------------- Main Application ------------------

class BankingSystemApp(tk.Tk):
    def __init__(self, bank: Bank):
        super().__init__()
        self.title("Student Banking System")
        self.geometry("1024x720")
        self.minsize(600, 480)
        self.bank = bank
        self.style = ttk.Style(self)
        self._setup_theme()

        self.header_frame = tk.Frame(self, height=64, bg="#1e293b")
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        self.sidebar_frame = tk.Frame(self, width=280, bg="#334155")
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.main_frame = tk.Frame(self, bg="#f1f5f9")
        self.main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.footer_frame = tk.Frame(self, height=40, bg="#1e293b")
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self._build_header()
        self._build_sidebar()
        self.current_view = None
        self._build_footer()
        self._show_home()
        self._bind_shortcuts()

    def _setup_theme(self):
        self.style.theme_use("clam")
        self.style.configure("TButton", font=("Segoe UI", 10), foreground="#f1f5f9", background="#334155", padding=8)
        self.style.map("TButton",
                       foreground=[("active", "#60a5fa")],
                       background=[("active", "#1e40af")])
        self.style.configure("TLabel", font=("Segoe UI", 11), foreground="#334155")
        self.style.configure("Treeview",
                             background="#f1f5f9",
                             fieldbackground="#f1f5f9",
                             foreground="#334155",
                             font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading",
                             font=("Segoe UI", 11, "bold"),
                             foreground="#1e293b")

    def _build_header(self):
        tk.Label(self.header_frame, text="🏦", font=("Segoe UI Emoji", 28), bg="#1e293b", fg="#60a5fa").pack(side=tk.LEFT, padx=16)
        tk.Label(self.header_frame, text="Student Bank", font=("Segoe UI", 20, "bold"), bg="#1e293b", fg="#e0e7ff").pack(side=tk.LEFT, padx=4)

        ttk.Button(self.header_frame, text="Home", command=self._show_home).pack(side=tk.RIGHT, padx=8)
        ttk.Button(self.header_frame, text="Settings", command=self._show_settings).pack(side=tk.RIGHT, padx=8)
        ttk.Button(self.header_frame, text="About", command=self._show_about).pack(side=tk.RIGHT, padx=8)
        

    def _build_sidebar(self):
        sidebar_items = [
            ("Home", self._show_home),
            ("Customer Management", self._show_customers),
            ("Account Management", self._show_accounts),
            ("Transfer Funds", self._show_transfer),
            ("Apply Interest", self._show_apply_interest),
            ("Reports", self._show_reports),
            ("Exit", self.quit),
        ]
        for text, cmd in sidebar_items:
            ttk.Button(self.sidebar_frame, text=text, command=cmd).pack(fill='x', pady=8, padx=10)

    def _build_footer(self):
        self.status_label = tk.Label(self.footer_frame, text="Ready", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, padx=10)
        current_year = datetime.datetime.now().year
        tk.Label(self.footer_frame, text=f"© {current_year} Student Bank. All rights reserved.", bg="#1e293b", fg="#64748b", font=("Segoe UI", 9)).pack(side=tk.RIGHT, padx=10)

    def _set_status(self, msg: str):
        self.status_label.config(text=msg)
        self.after(5000, lambda: self.status_label.config(text="Ready"))

    def _clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _show_home(self):
        self._clear_main_frame()
        self.current_view = HomeView(self.main_frame, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Home loaded")

    def _show_customers(self):
        self._clear_main_frame()
        self.current_view = CustomerManagementView(self.main_frame, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Customer Management loaded")

    def _show_accounts(self):
        self._clear_main_frame()
        from_account_view = AccountManagementView(self.main_frame, self)
        self.current_view = from_account_view
        from_account_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Account Management loaded")

    def _show_transfer(self):
        self._clear_main_frame()
        self.current_view = TransferFundsView(self.main_frame, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Transfer Funds loaded")

    def _show_apply_interest(self):
        self._clear_main_frame()
        self.current_view = ApplyInterestView(self.main_frame, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Apply Interest loaded")

    def _show_reports(self):
        self._clear_main_frame()
        self.current_view = ReportView(self.main_frame, self)
        self.current_view.pack(fill=tk.BOTH, expand=True)
        self._set_status("Reports loaded")

    def _show_settings(self):
        self._clear_main_frame()
        label = tk.Label(self.main_frame, text="You are not authorized to change settings.", font=("Segoe UI", 14))
        label.pack(pady=20)
        self._set_status("Settings loaded")

    def _show_about(self):
        self._clear_main_frame()
        label = tk.Label(self.main_frame, text="About Student Banking System\nVersion 1.0", font=("Segoe UI", 14))
        label.pack(pady=20)
        self._set_status("About page loaded")

    def _bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self._show_customers())
        self.bind("<Control-q>", lambda e: self.quit())

def main():
    bank = Bank()
    app = BankingSystemApp(bank)
    app.mainloop()

if __name__ == "__main__":
    main()      
