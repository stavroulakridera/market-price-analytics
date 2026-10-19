"""Local authentication for a PRIVATE Streamlit deployment.
Database must live on durable, access-restricted storage; do not deploy with real data on public Community Cloud.
"""
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

PH = PasswordHasher()
DB_PATH = Path(os.environ.get('MPA_AUTH_DB', 'data/users.sqlite3'))
SESSION_SECONDS = 30 * 60


def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=15000')
    return conn


def init_auth():
    with _db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY COLLATE NOCASE,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin','analyst')),
            active INTEGER NOT NULL DEFAULT 1,
            must_change INTEGER NOT NULL DEFAULT 1,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            at TEXT NOT NULL, actor TEXT NOT NULL,
            action TEXT NOT NULL, target TEXT NOT NULL
        )''')
        count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if count == 0:
            username = os.environ.get('MPA_BOOTSTRAP_ADMIN_USERNAME', '').strip().lower()
            password = os.environ.get('MPA_BOOTSTRAP_ADMIN_PASSWORD', '')
            if username and len(password) >= 12 and re.fullmatch(r'[a-zA-Z0-9_.-]{3,50}', username):
                conn.execute('INSERT INTO users VALUES (?,?,?,?,1,1,0,0,?)',
                             (username, 'Διαχειριστής', PH.hash(password), 'admin', _now()))
                _audit(conn, username, 'bootstrap_admin', username)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _audit(conn, actor, action, target):
    conn.execute('INSERT INTO audit(at,actor,action,target) VALUES(?,?,?,?)', (_now(), actor, action, target))


def get_user(username):
    with _db() as conn:
        row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        return dict(row) if row else None


def authenticate(username, password):
    username = username.strip().lower()
    with _db() as conn:
        row = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if not row or not row['active'] or row['locked_until'] > time.time():
            return False
        try:
            PH.verify(row['password_hash'], password)
        except (VerifyMismatchError, VerificationError):
            fails = row['failed_attempts'] + 1
            lock = time.time() + 15 * 60 if fails >= 5 else 0
            conn.execute('UPDATE users SET failed_attempts=?, locked_until=? WHERE username=?', (fails, lock, username))
            return False
        conn.execute('UPDATE users SET failed_attempts=0, locked_until=0 WHERE username=?', (username,))
        _audit(conn, username, 'login', username)
        return True


def change_password(username, old, new):
    if len(new) < 12 or len(new) > 256 or new == old:
        return False
    user = get_user(username)
    if not user or not user['active']:
        return False
    try:
        PH.verify(user['password_hash'], old)
    except (VerifyMismatchError, VerificationError):
        return False
    with _db() as conn:
        conn.execute('UPDATE users SET password_hash=?, must_change=0 WHERE username=?', (PH.hash(new), username))
        _audit(conn, username, 'password_changed', username)
    return True


def create_user(actor, username, full_name, password, role):
    username = username.strip().lower()
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,50}', username):
        raise ValueError('Username: 3–50 λατινικοί χαρακτήρες, αριθμοί, _ . -')
    if not full_name.strip() or len(password) < 12 or role not in ('admin', 'analyst'):
        raise ValueError('Απαιτείται όνομα, ρόλος και προσωρινός κωδικός τουλάχιστον 12 χαρακτήρων.')
    with _db() as conn:
        conn.execute('INSERT INTO users VALUES (?,?,?,?,1,1,0,0,?)',
                     (username, full_name.strip(), PH.hash(password), role, _now()))
        _audit(conn, actor, 'user_created', username)


def update_user(actor, username, active, role, temporary_password=None):
    if role not in ('admin', 'analyst'):
        raise ValueError('Μη έγκυρος ρόλος')
    with _db() as conn:
        target = conn.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if not target:
            raise ValueError('Ο χρήστης δεν υπάρχει')
        if username == actor and (not active or role != 'admin'):
            raise ValueError('Δεν μπορείς να απενεργοποιήσεις ή να υποβαθμίσεις τον δικό σου Admin λογαριασμό.')
        if target['role'] == 'admin' and (not active or role != 'admin'):
            admins = conn.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1").fetchone()[0]
            if admins <= 1:
                raise ValueError('Πρέπει να παραμείνει τουλάχιστον ένας ενεργός Admin.')
        conn.execute('UPDATE users SET active=?, role=?, failed_attempts=0, locked_until=0 WHERE username=?',
                     (int(active), role, username))
        if temporary_password:
            if len(temporary_password) < 12:
                raise ValueError('Ο προσωρινός κωδικός χρειάζεται τουλάχιστον 12 χαρακτήρες.')
            conn.execute('UPDATE users SET password_hash=?, must_change=1 WHERE username=?',
                         (PH.hash(temporary_password), username))
        _audit(conn, actor, 'user_updated', username)


def users_table():
    with _db() as conn:
        return [dict(r) for r in conn.execute('SELECT username,full_name,role,active,must_change,created_at FROM users ORDER BY username')]


def audit_table():
    with _db() as conn:
        return [dict(r) for r in conn.execute('SELECT at,actor,action,target FROM audit ORDER BY id DESC LIMIT 100')]


def require_login():
    init_auth()
    username = st.session_state.get('auth_username')
    if username:
        user = get_user(username)
        if not user or not user['active'] or time.time() - st.session_state.get('auth_last_seen', 0) > SESSION_SECONDS:
            st.session_state.pop('auth_username', None)
            st.session_state.pop('auth_last_seen', None)
        else:
            st.session_state.auth_last_seen = time.time()
            if user['must_change']:
                st.title('🔑 Υποχρεωτική αλλαγή κωδικού')
                st.info('Πριν συνεχίσεις, άλλαξε τον προσωρινό κωδικό σου.')
                with st.form('first_password_change'):
                    old = st.text_input('Προσωρινός κωδικός', type='password')
                    new = st.text_input('Νέος κωδικός (τουλάχιστον 12 χαρακτήρες)', type='password')
                    repeat = st.text_input('Επιβεβαίωση νέου κωδικού', type='password')
                    submitted = st.form_submit_button('Αλλαγή κωδικού')
                if submitted:
                    if new != repeat:
                        st.error('Οι νέοι κωδικοί δεν συμφωνούν.')
                    elif change_password(username, old, new):
                        st.success('Ο κωδικός άλλαξε.')
                        st.rerun()
                    else:
                        st.error('Ελέγξτε τον προσωρινό και τον νέο κωδικό.')
                st.stop()
            return user
    st.title('🔐 Market Price Analytics')
    st.subheader('Σύνδεση υπαλλήλου')
    with st.form('login_form'):
        username = st.text_input('Username')
        password = st.text_input('Password', type='password')
        submitted = st.form_submit_button('Είσοδος')
    if submitted:
        if authenticate(username, password):
            st.session_state.auth_username = username.strip().lower()
            st.session_state.auth_last_seen = time.time()
            st.rerun()
        else:
            st.error('Λανθασμένα στοιχεία ή προσωρινά κλειδωμένος λογαριασμός.')
    with _db() as conn:
        if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            st.error('Δεν έχει οριστεί αρχικός Admin. Ρύθμισε τα MPA_BOOTSTRAP_ADMIN_USERNAME και MPA_BOOTSTRAP_ADMIN_PASSWORD στο ιδιωτικό περιβάλλον του server.')
    st.stop()


def admin_screen(current_user):
    if current_user['role'] != 'admin':
        st.error('Δεν έχεις δικαίωμα διαχείρισης χρηστών.')
        st.stop()
    st.title('👥 Διαχείριση Χρηστών')
    st.dataframe(users_table(), use_container_width=True, hide_index=True)
    with st.expander('➕ Δημιουργία λογαριασμού'):
        with st.form('new_user', clear_on_submit=True):
            username = st.text_input('Username (λατινικοί χαρακτήρες)')
            full_name = st.text_input('Ονοματεπώνυμο')
            role = st.selectbox('Ρόλος', ['analyst', 'admin'])
            password = st.text_input('Προσωρινός κωδικός', type='password')
            submit = st.form_submit_button('Δημιουργία')
        if submit:
            try:
                create_user(current_user['username'], username, full_name, password, role)
                st.success('Ο λογαριασμός δημιουργήθηκε. Ο χρήστης πρέπει να αλλάξει κωδικό στην πρώτη είσοδο.')
                st.rerun()
            except (ValueError, sqlite3.IntegrityError) as exc:
                st.error(str(exc))
    with st.expander('✏️ Επεξεργασία / επαναφορά κωδικού'):
        options = [u['username'] for u in users_table()]
        if options:
            target_name = st.selectbox('Χρήστης', options)
            target = get_user(target_name)
            with st.form('edit_user'):
                role = st.selectbox('Ρόλος', ['analyst', 'admin'], index=0 if target['role']=='analyst' else 1)
                active = st.checkbox('Ενεργός', value=bool(target['active']))
                password = st.text_input('Νέος προσωρινός κωδικός (προαιρετικά)', type='password')
                submit = st.form_submit_button('Αποθήκευση')
            if submit:
                try:
                    update_user(current_user['username'], target_name, active, role, password or None)
                    st.success('Οι αλλαγές αποθηκεύτηκαν.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander('🕘 Ιστορικό διαχείρισης λογαριασμών'):
        st.dataframe(audit_table(), use_container_width=True, hide_index=True)
