import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g, flash


app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_bella123'
DATABASE = 'consultorio.db'

# ---------------------- Conexão com o banco de dados ------------------------
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ---------------------- Inicializa o banco de dados -------------------------
def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            data_nascimento TEXT NOT NULL,
            telefone TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            especialidade TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_exame TEXT NOT NULL,
            id_medico INTEGER,
            FOREIGN KEY (id_medico) REFERENCES medicos(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exames_marcados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_medico INTEGER NOT NULL,
            id_exame INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'Agendado',
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
            FOREIGN KEY (id_medico) REFERENCES medicos(id),
            FOREIGN KEY (id_exame) REFERENCES exames(id)
        )
    ''')
    db.commit()

# ---------------------- Página Inicial --------------------------------------
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    agendamentos = db.execute('''
        SELECT a.*, m.nome_completo as medico_nome, e.nome_exame 
        FROM exames_marcados a
        LEFT JOIN medicos m ON a.id_medico = m.id
        LEFT JOIN exames e ON a.id_exame = e.id
        WHERE a.id_usuario = ?
        ORDER BY a.data_hora DESC
    ''', (session['usuario_id'],)).fetchall()
    
    return render_template('index.html', agendamentos=agendamentos)

# ---------------------- Formulários sem Validação -------------------------

# ---------------------- Cadastro de Usuário ---------------------------------
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        email = request.form['email']
        senha = request.form['senha']
        data_nascimento = request.form['data_nascimento']
        telefone = request.form['telefone']

        db = get_db()
        try:
            db.execute('INSERT INTO usuarios (nome_completo, cpf, email, senha, data_nascimento, telefone) VALUES (?, ?, ?, ?, ?, ?)', (nome, cpf, email, senha, data_nascimento, telefone))
            db.commit()
            flash('Cadastro realizado com sucesso! Faça login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Erro: CPF ou e-mail já cadastrado!')
            return render_template('cadastro.html')

    return render_template('cadastro.html')

# ---------------------- Login de Usuário ------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        cpf = request.form['cpf']
        senha = request.form['senha']
        print(cpf, senha)

        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE cpf = ? AND senha = ?',(cpf,senha)).fetchone()

        if usuario: 
            session['usuario_id'] = usuario['id']
            session['usuario_nome'] = usuario['nome_completo']
            return redirect(url_for('index'))
        else:
            flash('CPF ou senha incorretos!')
            return render_template('login.html')

    return render_template('login.html')

# ---------------------- Logout ----------------------------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------- Executar App ----------------------------------------
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
