import sys
import sqlite3
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                              QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget, 
                              QTableWidgetItem, QMessageBox, QStackedWidget, QFormLayout,
                              QTabWidget, QFrame, QFileDialog)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSet, QBarSeries, QBarCategoryAxis
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import csv
from fpdf import FPDF
import hashlib

class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Gerenciador de Orçamento")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout()
        
        self.title_label = QLabel("Gerenciador de Orçamento Pessoal")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle_label = QLabel("Faça login para continuar")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.register_button = QPushButton("Criar nova conta")
        self.register_button.setStyleSheet("color: #4CAF50;")
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        
        self.setLayout(layout)
        
        # Conexão com o banco de dados
        self.conn = sqlite3.connect('budget_manager.db')
        self.cursor = self.conn.cursor()
        
        # Criar tabela de usuários se não existir
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        ''')
        self.conn.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle(f"Gerenciador de Orçamento - {username}")
        self.setMinimumSize(800, 600)
        
        # Configuração do banco de dados
        self.conn = sqlite3.connect('budget_manager.db')
        self.cursor = self.conn.cursor()
        
        # Criar tabelas se não existirem
        self.create_tables()
        
        # Configuração da interface
        self.setup_ui()
        
        # Carregar dados iniciais
        self.load_initial_data()
        
        # Aplicar dark mode por padrão
        self.apply_dark_theme(True)
        
    def create_tables(self):
        # Tabela de despesas fixas
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fixed_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT,
                amount REAL,
                due_day INTEGER,
                category TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de despesas variáveis
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS variable_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                description TEXT,
                amount REAL,
                date TEXT,
                category TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Tabela de renda mensal
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL,
                month_year TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        self.conn.commit()
    
    def setup_ui(self):
        # Widget central e layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de navegação superior
        self.setup_top_navigation(main_layout)
        
        # Widget de abas para as diferentes seções
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Configurar as abas
        self.setup_dashboard_tab()
        self.setup_fixed_expenses_tab()
        self.setup_variable_expenses_tab()
        self.setup_income_tab()
        self.setup_reports_tab()
        
        # Barra de status
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Pronto")
    
    def setup_top_navigation(self, main_layout):
        nav_frame = QFrame()
        nav_frame.setFrameShape(QFrame.Shape.StyledPanel)
        nav_layout = QHBoxLayout(nav_frame)
        
        self.dashboard_btn = QPushButton("Dashboard")
        self.fixed_expenses_btn = QPushButton("Despesas Fixas")
        self.variable_expenses_btn = QPushButton("Despesas Variáveis")
        self.income_btn = QPushButton("Renda")
        self.reports_btn = QPushButton("Relatórios")
        
        self.theme_toggle = QPushButton("Alternar Tema")
        self.logout_btn = QPushButton("Sair")
        
        # Adicionar botões ao layout
        nav_layout.addWidget(self.dashboard_btn)
        nav_layout.addWidget(self.fixed_expenses_btn)
        nav_layout.addWidget(self.variable_expenses_btn)
        nav_layout.addWidget(self.income_btn)
        nav_layout.addWidget(self.reports_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.theme_toggle)
        nav_layout.addWidget(self.logout_btn)
        
        main_layout.addWidget(nav_frame)
        
        # Conectar botões
        self.dashboard_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(0))
        self.fixed_expenses_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        self.variable_expenses_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        self.income_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))
        self.reports_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(4))
        self.theme_toggle.clicked.connect(self.toggle_theme)
        self.logout_btn.clicked.connect(self.logout)
    
    def setup_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Seção de resumo
        summary_frame = QFrame()
        summary_frame.setFrameShape(QFrame.Shape.StyledPanel)
        summary_layout = QHBoxLayout(summary_frame)
        
        self.income_label = QLabel("Renda Mensal: R$ 0.00")
        self.fixed_expenses_label = QLabel("Despesas Fixas: R$ 0.00")
        self.variable_expenses_label = QLabel("Despesas Variáveis: R$ 0.00")
        self.balance_label = QLabel("Saldo: R$ 0.00")
        
        for label in [self.income_label, self.fixed_expenses_label, 
                     self.variable_expenses_label, self.balance_label]:
            label.setStyleSheet("font-size: 14px; font-weight: bold;")
            summary_layout.addWidget(label)
        
        layout.addWidget(summary_frame)
        
        # Seção de gráficos
        charts_frame = QFrame()
        charts_layout = QHBoxLayout(charts_frame)
        
        # Gráfico de pizza para despesas
        self.expenses_pie_chart = QChart()
        self.expenses_pie_chart.setTitle("Distribuição de Despesas")
        self.expenses_pie_chart_view = QChartView(self.expenses_pie_chart)
        
        # Gráfico de barras para histórico
        self.history_bar_chart = QChart()
        self.history_bar_chart.setTitle("Histórico de Gastos")
        self.history_bar_chart_view = QChartView(self.history_bar_chart)
        
        charts_layout.addWidget(self.expenses_pie_chart_view)
        charts_layout.addWidget(self.history_bar_chart_view)
        
        layout.addWidget(charts_frame)
        
        # Seção de sugestões
        self.suggestions_label = QLabel()
        self.suggestions_label.setWordWrap(True)
        layout.addWidget(self.suggestions_label)
        
        self.tab_widget.addTab(tab, "Dashboard")
    
    def setup_fixed_expenses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário para adicionar despesas fixas
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.fixed_desc_input = QLineEdit()
        self.fixed_amount_input = QLineEdit()
        self.fixed_due_day_input = QLineEdit()
        self.fixed_category_input = QComboBox()
        self.fixed_category_input.addItems(["Moradia", "Utilidades", "Transporte", "Alimentação", "Saúde", "Lazer", "Outros"])
        
        form_layout.addRow("Descrição:", self.fixed_desc_input)
        form_layout.addRow("Valor (R$):", self.fixed_amount_input)
        form_layout.addRow("Dia de Vencimento:", self.fixed_due_day_input)
        form_layout.addRow("Categoria:", self.fixed_category_input)
        
        self.add_fixed_expense_btn = QPushButton("Adicionar Despesa Fixa")
        form_layout.addRow(self.add_fixed_expense_btn)
        
        layout.addWidget(form_frame)
        
        # Tabela de despesas fixas
        self.fixed_expenses_table = QTableWidget()
        self.fixed_expenses_table.setColumnCount(5)
        self.fixed_expenses_table.setHorizontalHeaderLabels(["ID", "Descrição", "Valor", "Dia Venc.", "Categoria"])
        self.fixed_expenses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.delete_fixed_expense_btn = QPushButton("Remover Despesa Selecionada")
        self.delete_fixed_expense_btn.setStyleSheet("background-color: #f44336; color: white;")
        
        layout.addWidget(self.fixed_expenses_table)
        layout.addWidget(self.delete_fixed_expense_btn)
        
        # Conectar sinais
        self.add_fixed_expense_btn.clicked.connect(self.add_fixed_expense)
        self.delete_fixed_expense_btn.clicked.connect(self.delete_fixed_expense)
        
        self.tab_widget.addTab(tab, "Despesas Fixas")
    
    def setup_variable_expenses_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário para adicionar despesas variáveis
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.var_desc_input = QLineEdit()
        self.var_amount_input = QLineEdit()
        self.var_date_input = QLineEdit()
        self.var_date_input.setText(QDate.currentDate().toString("dd/MM/yyyy"))
        self.var_category_input = QComboBox()
        self.var_category_input.addItems(["Alimentação", "Transporte", "Lazer", "Compras", "Saúde", "Outros"])
        
        form_layout.addRow("Descrição:", self.var_desc_input)
        form_layout.addRow("Valor (R$):", self.var_amount_input)
        form_layout.addRow("Data:", self.var_date_input)
        form_layout.addRow("Categoria:", self.var_category_input)
        
        self.add_var_expense_btn = QPushButton("Adicionar Despesa Variável")
        form_layout.addRow(self.add_var_expense_btn)
        
        layout.addWidget(form_frame)
        
        # Filtros
        filter_frame = QFrame()
        filter_layout = QHBoxLayout(filter_frame)
        
        self.filter_month_input = QComboBox()
        months = ["Todos"] + [f"{m:02d}" for m in range(1, 13)]
        self.filter_month_input.addItems(months)
        self.filter_month_input.setCurrentIndex(QDate.currentDate().month())
        
        self.filter_year_input = QComboBox()
        current_year = QDate.currentDate().year()
        years = ["Todos"] + [str(y) for y in range(current_year - 2, current_year + 1)]
        self.filter_year_input.addItems(years)
        self.filter_year_input.setCurrentText(str(current_year))
        
        self.filter_category_input = QComboBox()
        self.filter_category_input.addItems(["Todas"] + ["Alimentação", "Transporte", "Lazer", "Compras", "Saúde", "Outros"])
        
        self.apply_filter_btn = QPushButton("Aplicar Filtros")
        
        filter_layout.addWidget(QLabel("Mês:"))
        filter_layout.addWidget(self.filter_month_input)
        filter_layout.addWidget(QLabel("Ano:"))
        filter_layout.addWidget(self.filter_year_input)
        filter_layout.addWidget(QLabel("Categoria:"))
        filter_layout.addWidget(self.filter_category_input)
        filter_layout.addWidget(self.apply_filter_btn)
        
        layout.addWidget(filter_frame)
        
        # Tabela de despesas variáveis
        self.var_expenses_table = QTableWidget()
        self.var_expenses_table.setColumnCount(5)
        self.var_expenses_table.setHorizontalHeaderLabels(["ID", "Descrição", "Valor", "Data", "Categoria"])
        self.var_expenses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        self.delete_var_expense_btn = QPushButton("Remover Despesa Selecionada")
        self.delete_var_expense_btn.setStyleSheet("background-color: #f44336; color: white;")
        
        layout.addWidget(self.var_expenses_table)
        layout.addWidget(self.delete_var_expense_btn)
        
        # Conectar sinais
        self.add_var_expense_btn.clicked.connect(self.add_variable_expense)
        self.delete_var_expense_btn.clicked.connect(self.delete_variable_expense)
        self.apply_filter_btn.clicked.connect(self.load_variable_expenses)
        
        self.tab_widget.addTab(tab, "Despesas Variáveis")
    
    def setup_income_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Formulário para adicionar renda
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.income_amount_input = QLineEdit()
        self.income_month_input = QComboBox()
        months = [f"{m:02d}/{QDate.currentDate().year()}" for m in range(1, 13)]
        self.income_month_input.addItems(months)
        self.income_month_input.setCurrentIndex(QDate.currentDate().month() - 1)
        
        form_layout.addRow("Valor (R$):", self.income_amount_input)
        form_layout.addRow("Mês/Ano:", self.income_month_input)
        
        self.add_income_btn = QPushButton("Adicionar Renda")
        form_layout.addRow(self.add_income_btn)
        
        layout.addWidget(form_frame)
        
        # Tabela de renda
        self.income_table = QTableWidget()
        self.income_table.setColumnCount(3)
        self.income_table.setHorizontalHeaderLabels(["ID", "Valor", "Mês/Ano"])
        
        layout.addWidget(self.income_table)
        
        # Conectar sinais
        self.add_income_btn.clicked.connect(self.add_income)
        
        self.tab_widget.addTab(tab, "Renda")
    
    def setup_reports_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Opções de relatório
        report_frame = QFrame()
        report_layout = QHBoxLayout(report_frame)
        
        self.report_type = QComboBox()
        self.report_type.addItems(["Relatório Mensal", "Relatório por Categoria", "Histórico de Gastos"])
        
        self.report_month = QComboBox()
        months = [f"{m:02d}/{QDate.currentDate().year()}" for m in range(1, 13)]
        self.report_month.addItems(months)
        self.report_month.setCurrentIndex(QDate.currentDate().month() - 1)
        
        self.generate_report_btn = QPushButton("Gerar Relatório")
        self.export_pdf_btn = QPushButton("Exportar PDF")
        self.export_csv_btn = QPushButton("Exportar CSV")
        
        report_layout.addWidget(QLabel("Tipo de Relatório:"))
        report_layout.addWidget(self.report_type)
        report_layout.addWidget(QLabel("Mês:"))
        report_layout.addWidget(self.report_month)
        report_layout.addWidget(self.generate_report_btn)
        report_layout.addWidget(self.export_pdf_btn)
        report_layout.addWidget(self.export_csv_btn)
        
        layout.addWidget(report_frame)
        
        # Área de visualização do relatório
        self.report_view = QLabel("Selecione as opções e clique em 'Gerar Relatório'")
        self.report_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.report_view.setWordWrap(True)
        
        layout.addWidget(self.report_view)
        
        # Conectar sinais
        self.generate_report_btn.clicked.connect(self.generate_report)
        self.export_pdf_btn.clicked.connect(self.export_to_pdf)
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        
        self.tab_widget.addTab(tab, "Relatórios")
    
    def load_initial_data(self):
        # Carregar dados do banco de dados
        self.load_fixed_expenses()
        self.load_variable_expenses()
        self.load_income()
        
        # Atualizar dashboard
        self.update_dashboard()
    
    def load_fixed_expenses(self):
        self.cursor.execute("SELECT id, description, amount, due_day, category FROM fixed_expenses WHERE user_id = ?", 
                          (self.get_user_id(),))
        fixed_expenses = self.cursor.fetchall()
        
        self.fixed_expenses_table.setRowCount(len(fixed_expenses))
        for row_idx, row_data in enumerate(fixed_expenses):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.fixed_expenses_table.setItem(row_idx, col_idx, item)
    
    def load_variable_expenses(self):
        month = self.filter_month_input.currentText()
        year = self.filter_year_input.currentText()
        category = self.filter_category_input.currentText()
        
        query = "SELECT id, description, amount, date, category FROM variable_expenses WHERE user_id = ?"
        params = [self.get_user_id()]
        
        if month != "Todos":
            query += " AND strftime('%m', date) = ?"
            params.append(month.zfill(2))
        
        if year != "Todos":
            query += " AND strftime('%Y', date) = ?"
            params.append(year)
        
        if category != "Todas":
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY date DESC"
        
        self.cursor.execute(query, params)
        var_expenses = self.cursor.fetchall()
        
        self.var_expenses_table.setRowCount(len(var_expenses))
        for row_idx, row_data in enumerate(var_expenses):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.var_expenses_table.setItem(row_idx, col_idx, item)
    
    def load_income(self):
        self.cursor.execute("SELECT id, amount, month_year FROM monthly_income WHERE user_id = ? ORDER BY month_year DESC", 
                          (self.get_user_id(),))
        income_data = self.cursor.fetchall()
        
        self.income_table.setRowCount(len(income_data))
        for row_idx, row_data in enumerate(income_data):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.income_table.setItem(row_idx, col_idx, item)
    
    def get_user_id(self):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (self.username,))
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def add_fixed_expense(self):
        description = self.fixed_desc_input.text().strip()
        amount = self.fixed_amount_input.text().strip()
        due_day = self.fixed_due_day_input.text().strip()
        category = self.fixed_category_input.currentText()
        
        if not all([description, amount, due_day]):
            QMessageBox.warning(self, "Campos Vazios", "Por favor, preencha todos os campos.")
            return
        
        try:
            amount = float(amount)
            due_day = int(due_day)
            
            if due_day < 1 or due_day > 31:
                raise ValueError("Dia inválido")
        except ValueError as e:
            QMessageBox.warning(self, "Valor Inválido", f"Por favor, insira valores válidos.\n{str(e)}")
            return
        
        user_id = self.get_user_id()
        self.cursor.execute(
            "INSERT INTO fixed_expenses (user_id, description, amount, due_day, category) VALUES (?, ?, ?, ?, ?)",
            (user_id, description, amount, due_day, category)
        )
        self.conn.commit()
        
        self.fixed_desc_input.clear()
        self.fixed_amount_input.clear()
        self.fixed_due_day_input.clear()
        
        self.load_fixed_expenses()
        self.update_dashboard()
        
        QMessageBox.information(self, "Sucesso", "Despesa fixa adicionada com sucesso!")
    
    def delete_fixed_expense(self):
        selected_rows = self.fixed_expenses_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma despesa para remover.")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.fixed_expenses_table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self, "Confirmar Remoção", 
            "Tem certeza que deseja remover esta despesa fixa?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM fixed_expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            self.load_fixed_expenses()
            self.update_dashboard()
    
    def add_variable_expense(self):
        description = self.var_desc_input.text().strip()
        amount = self.var_amount_input.text().strip()
        date_str = self.var_date_input.text().strip()
        category = self.var_category_input.currentText()
        
        if not all([description, amount, date_str]):
            QMessageBox.warning(self, "Campos Vazios", "Por favor, preencha todos os campos.")
            return
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("O valor deve ser positivo")
                
            # Validar e formatar a data para o padrão SQLite (YYYY-MM-DD)
            try:
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                sqlite_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                QMessageBox.warning(self, "Data Inválida", "Formato de data inválido. Use DD/MM/AAAA.")
                return
                
        except ValueError as e:
            QMessageBox.warning(self, "Valor Inválido", f"Por favor, insira valores válidos.\n{str(e)}")
            return
        
        user_id = self.get_user_id()
        try:
            self.cursor.execute(
                "INSERT INTO variable_expenses (user_id, description, amount, date, category) VALUES (?, ?, ?, ?, ?)",
                (user_id, description, amount, sqlite_date, category)
            )
            self.conn.commit()
            
            self.var_desc_input.clear()
            self.var_amount_input.clear()
            self.var_date_input.setText(QDate.currentDate().toString("dd/MM/yyyy"))
            
            self.load_variable_expenses()
            self.update_dashboard()
            
            QMessageBox.information(self, "Sucesso", "Despesa variável adicionada com sucesso!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Erro no Banco de Dados", f"Não foi possível adicionar a despesa:\n{str(e)}")
            self.conn.rollback()
    
    def delete_variable_expense(self):
        selected_rows = self.var_expenses_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Nenhuma Seleção", "Por favor, selecione uma despesa para remover.")
            return
        
        row = selected_rows[0].row()
        expense_id = int(self.var_expenses_table.item(row, 0).text())
        
        reply = QMessageBox.question(
            self, "Confirmar Remoção", 
            "Tem certeza que deseja remover esta despesa variável?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.cursor.execute("DELETE FROM variable_expenses WHERE id = ?", (expense_id,))
            self.conn.commit()
            self.load_variable_expenses()
            self.update_dashboard()
    
    def add_income(self):
        amount = self.income_amount_input.text().strip()
        month_year = self.income_month_input.currentText()
        
        if not amount:
            QMessageBox.warning(self, "Campo Vazio", "Por favor, informe o valor da renda.")
            return
        
        try:
            amount = float(amount)
        except ValueError:
            QMessageBox.warning(self, "Valor Inválido", "Por favor, insira um valor numérico válido.")
            return
        
        user_id = self.get_user_id()
        
        # Verificar se já existe registro para este mês/ano
        self.cursor.execute(
            "SELECT id FROM monthly_income WHERE user_id = ? AND month_year = ?",
            (user_id, month_year)
        )
        existing = self.cursor.fetchone()
        
        if existing:
            reply = QMessageBox.question(
                self, "Registro Existente",
                "Já existe um registro de renda para este mês. Deseja atualizá-lo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.cursor.execute(
                    "UPDATE monthly_income SET amount = ? WHERE id = ?",
                    (amount, existing[0])
                )
                self.conn.commit()
        else:
            self.cursor.execute(
                "INSERT INTO monthly_income (user_id, amount, month_year) VALUES (?, ?, ?)",
                (user_id, amount, month_year)
            )
            self.conn.commit()
        
        self.income_amount_input.clear()
        self.load_income()
        self.update_dashboard()
        
        QMessageBox.information(self, "Sucesso", "Renda mensal atualizada com sucesso!")
    
    def update_dashboard(self):
        # Calcular totais
        user_id = self.get_user_id()
        
        # Renda do mês atual
        current_month = QDate.currentDate().toString("MM/yyyy")
        self.cursor.execute(
            "SELECT amount FROM monthly_income WHERE user_id = ? AND month_year = ?",
            (user_id, current_month)
        )
        income_result = self.cursor.fetchone()
        income = income_result[0] if income_result else 0.0
        
        # Despesas fixas
        self.cursor.execute(
            "SELECT SUM(amount) FROM fixed_expenses WHERE user_id = ?",
            (user_id,)
        )
        fixed_expenses = self.cursor.fetchone()[0] or 0.0
        
        # Despesas variáveis do mês atual
        self.cursor.execute(
            "SELECT SUM(amount) FROM variable_expenses WHERE user_id = ? AND strftime('%m/%Y', date) = ?",
            (user_id, current_month)
        )
        var_expenses = self.cursor.fetchone()[0] or 0.0
        
        # Atualizar labels
        self.income_label.setText(f"Renda Mensal: R$ {income:,.2f}")
        self.fixed_expenses_label.setText(f"Despesas Fixas: R$ {fixed_expenses:,.2f}")
        self.variable_expenses_label.setText(f"Despesas Variáveis: R$ {var_expenses:,.2f}")
        
        balance = income - fixed_expenses - var_expenses
        self.balance_label.setText(f"Saldo: R$ {balance:,.2f}")
        
        # Atualizar gráficos
        self.update_charts()
        
        # Gerar sugestões
        self.generate_suggestions(income, fixed_expenses, var_expenses)
    
    def update_charts(self):
        user_id = self.get_user_id()
        current_month = QDate.currentDate().toString("MM/yyyy")
        
        # Gráfico de pizza - Distribuição de despesas
        self.cursor.execute(
            "SELECT category, SUM(amount) FROM variable_expenses WHERE user_id = ? AND strftime('%m/%Y', date) = ? GROUP BY category",
            (user_id, current_month)
        )
        var_expenses_by_category = self.cursor.fetchall()
        
        pie_series = QPieSeries()
        pie_series.setPieSize(0.7)
        
        for category, amount in var_expenses_by_category:
            if amount > 0:
                slice = pie_series.append(f"{category} (R${amount:,.2f})", amount)
                slice.setLabelVisible()
        
        self.expenses_pie_chart.removeAllSeries()
        self.expenses_pie_chart.addSeries(pie_series)
        self.expenses_pie_chart.setTitle("Distribuição de Despesas Variáveis")
        
        # Gráfico de barras - Histórico de gastos
        self.cursor.execute(
            "SELECT strftime('%m/%Y', date) as month, SUM(amount) FROM variable_expenses WHERE user_id = ? GROUP BY month ORDER BY date DESC LIMIT 6",
            (user_id,)
        )
        last_months_expenses = self.cursor.fetchall()
        
        if last_months_expenses:
            bar_set = QBarSet("Gastos Mensais")
            categories = []
            
            for month, amount in reversed(last_months_expenses):
                bar_set.append(amount)
                categories.append(month)
            
            bar_series = QBarSeries()
            bar_series.append(bar_set)
            
            self.history_bar_chart.removeAllSeries()
            self.history_bar_chart.addSeries(bar_series)
            
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            self.history_bar_chart.setAxisX(axis_x, bar_series)
            
            self.history_bar_chart.setTitle("Histórico de Gastos (Últimos 6 meses)")
    
    def generate_suggestions(self, income, fixed_expenses, var_expenses):
        suggestions = []
        
        total_expenses = fixed_expenses + var_expenses
        savings_rate = (income - total_expenses) / income * 100 if income > 0 else 0
        
        if savings_rate < 10:
            suggestions.append("💡 Você está economizando menos de 10% da sua renda. Tente aumentar sua taxa de poupança.")
        
        if var_expenses > income * 0.3:
            suggestions.append("⚠️ Seus gastos variáveis estão acima de 30% da sua renda. Considere reduzir despesas não essenciais.")
        
        # Analisar categorias com maiores gastos
        user_id = self.get_user_id()
        current_month = QDate.currentDate().toString("MM/yyyy")
        
        self.cursor.execute(
            "SELECT category, SUM(amount) FROM variable_expenses WHERE user_id = ? AND strftime('%m/%Y', date) = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id, current_month)
        )
        top_category = self.cursor.fetchone()
        
        if top_category and top_category[1] > income * 0.2:
            suggestions.append(f"🔍 Sua maior categoria de gastos é '{top_category[0]}', consumindo {top_category[1]/income*100:.1f}% da sua renda. Avalie se esses gastos podem ser reduzidos.")
        
        if not suggestions:
            suggestions.append("✅ Seus gastos estão bem balanceados. Continue assim!")
        
        self.suggestions_label.setText("\n".join(suggestions))
    
    def generate_report(self):
        report_type = self.report_type.currentText()
        month_year = self.report_month.currentText()
        
        user_id = self.get_user_id()
        
        if report_type == "Relatório Mensal":
            # Obter renda do mês
            self.cursor.execute(
                "SELECT amount FROM monthly_income WHERE user_id = ? AND month_year = ?",
                (user_id, month_year)
            )
            income = self.cursor.fetchone()
            income = income[0] if income else 0.0
            
            # Obter despesas fixas
            fixed_expenses = 0.0
            self.cursor.execute(
                "SELECT description, amount, due_day FROM fixed_expenses WHERE user_id = ?",
                (user_id,)
            )
            fixed_expenses_data = self.cursor.fetchall()
            
            fixed_details = []
            for desc, amount, due_day in fixed_expenses_data:
                fixed_details.append(f"{desc}: R$ {amount:,.2f} (vencimento dia {due_day})")
                fixed_expenses += amount
            
            # Obter despesas variáveis por categoria
            self.cursor.execute(
                "SELECT category, SUM(amount) FROM variable_expenses WHERE user_id = ? AND strftime('%m/%Y', date) = ? GROUP BY category",
                (user_id, month_year)
            )
            var_expenses_by_category = self.cursor.fetchall()
            var_expenses = sum(amount for _, amount in var_expenses_by_category)
            
            # Construir relatório
            report_text = f"📊 Relatório Mensal - {month_year}\n\n"
            report_text += f"Renda: R$ {income:,.2f}\n"
            report_text += f"Despesas Fixas: R$ {fixed_expenses:,.2f}\n"
            report_text += "Detalhes:\n- " + "\n- ".join(fixed_details) + "\n\n"
            report_text += f"Despesas Variáveis: R$ {var_expenses:,.2f}\n"
            report_text += "Por Categoria:\n"
            
            for category, amount in var_expenses_by_category:
                report_text += f"- {category}: R$ {amount:,.2f}\n"
            
            balance = income - fixed_expenses - var_expenses
            report_text += f"\nSaldo Final: R$ {balance:,.2f}\n"
            
            if balance > 0:
                report_text += "✅ Você terminou o mês com saldo positivo!"
            else:
                report_text += "⚠️ Atenção: seu saldo está negativo este mês."
            
            self.report_view.setText(report_text)
        
        elif report_type == "Relatório por Categoria":
            # Obter média de gastos por categoria nos últimos 3 meses
            self.cursor.execute(
                """
                SELECT category, AVG(monthly_sum) as avg_monthly
                FROM (
                    SELECT category, strftime('%m/%Y', date) as month, SUM(amount) as monthly_sum
                    FROM variable_expenses
                    WHERE user_id = ? AND date >= date('now', '-3 months')
                    GROUP BY category, month
                ) GROUP BY category
                """,
                (user_id,)
            )
            category_avg = self.cursor.fetchall()
            
            report_text = f"📈 Relatório por Categoria (Média dos Últimos 3 Meses)\n\n"
            
            for category, avg in category_avg:
                report_text += f"- {category}: R$ {avg:,.2f}/mês\n"
            
            self.report_view.setText(report_text)
        
        elif report_type == "Histórico de Gastos":
            # Obter histórico dos últimos 6 meses
            self.cursor.execute(
                """
                SELECT strftime('%m/%Y', date) as month, SUM(amount)
                FROM variable_expenses
                WHERE user_id = ?
                GROUP BY month
                ORDER BY date DESC
                LIMIT 6
                """,
                (user_id,)
            )
            history = self.cursor.fetchall()
            
            report_text = "📅 Histórico de Gastos (Últimos 6 Meses)\n\n"
            
            for month, amount in reversed(history):
                report_text += f"- {month}: R$ {amount:,.2f}\n"
            
            self.report_view.setText(report_text)
    
    def export_to_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exportar para PDF", "", "PDF Files (*.pdf)", options=options)
        
        if file_name:
            if not file_name.endswith('.pdf'):
                file_name += '.pdf'
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Adicionar título
            pdf.cell(200, 10, txt="Relatório de Orçamento Pessoal", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Usuário: {self.username}", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1, align='C')
            pdf.ln(10)
            
            # Adicionar conteúdo do relatório
            report_text = self.report_view.text()
            for line in report_text.split('\n'):
                pdf.cell(0, 10, txt=line, ln=1)
            
            pdf.output(file_name)
            QMessageBox.information(self, "Sucesso", f"Relatório exportado para:\n{file_name}")
    
    def export_to_csv(self):
        report_type = self.report_type.currentText()
        month_year = self.report_month.currentText()
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exportar para CSV", "", "CSV Files (*.csv)", options=options)
        
        if not file_name:
            return
        
        if not file_name.endswith('.csv'):
            file_name += '.csv'
        
        user_id = self.get_user_id()
        
        try:
            with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                if report_type == "Relatório Mensal":
                    writer.writerow(["Tipo", "Descrição", "Valor (R$)", "Data/Dia"])
                    
                    # Renda
                    self.cursor.execute(
                        "SELECT amount FROM monthly_income WHERE user_id = ? AND month_year = ?",
                        (user_id, month_year)
                    )
                    income = self.cursor.fetchone()
                    if income:
                        writer.writerow(["Renda", "Renda Mensal", f"{income[0]:.2f}", month_year])
                    
                    # Despesas fixas
                    self.cursor.execute(
                        "SELECT description, amount, due_day FROM fixed_expenses WHERE user_id = ?",
                        (user_id,)
                    )
                    for desc, amount, due_day in self.cursor.fetchall():
                        writer.writerow(["Despesa Fixa", desc, f"{amount:.2f}", f"Dia {due_day}"])
                    
                    # Despesas variáveis
                    self.cursor.execute(
                        "SELECT description, amount, date, category FROM variable_expenses WHERE user_id = ? AND strftime('%m/%Y', date) = ?",
                        (user_id, month_year)
                    )
                    for desc, amount, date, category in self.cursor.fetchall():
                        writer.writerow(["Despesa Variável", f"{desc} ({category})", f"{amount:.2f}", date])
                
                elif report_type == "Relatório por Categoria":
                    writer.writerow(["Categoria", "Média Mensal (Últimos 3 meses)"])
                    
                    self.cursor.execute(
                        """
                        SELECT category, AVG(monthly_sum) as avg_monthly
                        FROM (
                            SELECT category, strftime('%m/%Y', date) as month, SUM(amount) as monthly_sum
                            FROM variable_expenses
                            WHERE user_id = ? AND date >= date('now', '-3 months')
                            GROUP BY category, month
                        ) GROUP BY category
                        """,
                        (user_id,)
                    )
                    for category, avg in self.cursor.fetchall():
                        writer.writerow([category, f"{avg:.2f}"])
                
                elif report_type == "Histórico de Gastos":
                    writer.writerow(["Mês", "Total de Gastos"])
                    
                    self.cursor.execute(
                        """
                        SELECT strftime('%m/%Y', date) as month, SUM(amount)
                        FROM variable_expenses
                        WHERE user_id = ?
                        GROUP BY month
                        ORDER BY date DESC
                        LIMIT 6
                        """,
                        (user_id,)
                    )
                    for month, amount in self.cursor.fetchall():
                        writer.writerow([month, f"{amount:.2f}"])
            
            QMessageBox.information(self, "Sucesso", f"Dados exportados para:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Ocorreu um erro ao exportar:\n{str(e)}")
    
    def toggle_theme(self):
        current_theme = getattr(self, 'dark_theme', True)
        self.apply_dark_theme(not current_theme)
    
    def apply_dark_theme(self, dark):
        self.dark_theme = dark
        
        if dark:
            # Dark theme
            palette = self.palette()
            palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(palette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            self.setPalette(palette)
            
            # Aplicar estilo para tabelas
            self.setStyleSheet("""
                QTableWidget {
                    background-color: #252525;
                    color: white;
                    gridline-color: #444;
                }
                QHeaderView::section {
                    background-color: #353535;
                    color: white;
                    padding: 4px;
                    border: 1px solid #444;
                }
                QTableWidget::item {
                    border: 1px solid #444;
                }
                QTableWidget::item:selected {
                    background-color: #2a82da;
                    color: black;
                }
            """)
        else:
            # Light theme
            self.setPalette(self.style().standardPalette())
            self.setStyleSheet("")
    
    def logout(self):
        self.close()
        self.login_window = LoginWindow()
        self.login_window.show()
    
    def closeEvent(self, event):
        self.conn.close()
        event.accept()

class BudgetManagerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Configurar estilo visual
        self.app.setStyle('Fusion')
        
        # Mostrar janela de login inicialmente
        self.login_window = LoginWindow()
        self.login_window.show()
        
        # Conectar sinais
        self.login_window.login_button.clicked.connect(self.handle_login)
        self.login_window.register_button.clicked.connect(self.handle_register)
        
        # Variável para armazenar a janela principal
        self.main_window = None
    
    def handle_login(self):
        username = self.login_window.username_input.text().strip()
        password = self.login_window.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self.login_window, "Campos Vazios", "Por favor, preencha todos os campos.")
            return
        
        hashed_password = self.login_window.hash_password(password)
        
        self.login_window.cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = self.login_window.cursor.fetchone()
        
        if user:
            self.login_window.close()
            self.main_window = MainWindow(username)
            self.main_window.show()
        else:
            QMessageBox.warning(self.login_window, "Login Falhou", "Usuário ou senha incorretos.")
    
    def handle_register(self):
        username = self.login_window.username_input.text().strip()
        password = self.login_window.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self.login_window, "Campos Vazios", "Por favor, preencha todos os campos.")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self.login_window, "Senha Fraca", "A senha deve ter pelo menos 6 caracteres.")
            return
        
        hashed_password = self.login_window.hash_password(password)
        
        try:
            self.login_window.cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            self.login_window.conn.commit()
            QMessageBox.information(self.login_window, "Sucesso", "Conta criada com sucesso! Faça login para continuar.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self.login_window, "Usuário Existente", "Este nome de usuário já está em uso.")
    
    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    budget_app = BudgetManagerApp()
    budget_app.run()