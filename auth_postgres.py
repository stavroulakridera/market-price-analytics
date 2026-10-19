"""PostgreSQL auth backend for the mpa schema. Synthetic accounts only in public demo."""
import re
import time
from datetime import datetime, timezone, timedelta

import streamlit as st
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from psycopg import errors
from psycopg.rows import dict_row
from db import connect

PH = PasswordHasher()
SESSION_SECONDS = 1800


def _audit(cur, actor, action, target):
    cur.execute("""INSERT INTO mpa.audit_logs (user_id,action,entity_type,entity_id,details)
                   VALUES ((SELECT id FROM mpa.users WHERE username=%s),%s,'user',%s,'{}'::jsonb)""",
                (actor, action, target))


def _admin_secret(name):
    return st.secrets.get(name, '')


def init_auth():
    """Seed only when users table is empty; never overwrite existing accounts."""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(90320261019)')
            cur.execute('SELECT COUNT(*) FROM mpa.users')
            if cur.fetchone()[0] != 0:
                return
            username = str(_admin_secret('MPA_BOOTSTRAP_ADMIN_USERNAME')).strip().lower()
            password = str(_admin_secret('MPA_BOOTSTRAP_ADMIN_PASSWORD'))
            if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,50}', username) or not (12 <= len(password) <= 256):
                return
            cur.execute("""INSERT INTO mpa.users
                (username,display_name,password_hash,role,is_active,must_change_password)
                VALUES (%s,%s,%s,'admin',true,true)""",
                (username, 'Διαχειριστής', PH.hash(password)))
            _audit(cur, username, 'bootstrap_admin', username)


def get_user(username):
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""SELECT id,username,display_name AS full_name,password_hash,role,
                        is_active AS active,must_change_password AS must_change,
                        failed_attempts,locked_until,created_at
                        FROM mpa.users WHERE username=%s""", (username.strip().lower(),))
            return cur.fetchone()


def authenticate(username, password):
    username = username.strip().lower()
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT * FROM mpa.users WHERE username=%s FOR UPDATE', (username,))
            row = cur.fetchone()
            if not row or not row['is_active'] or (row['locked_until'] and row['locked_until'] > datetime.now(timezone.utc)):
                return False
            try:
                PH.verify(row['password_hash'], password)
            except (VerifyMismatchError, VerificationError):
                fails = row['failed_attempts'] + 1
                until = datetime.now(timezone.utc) + timedelta(minutes=15) if fails >= 5 else None
                cur.execute('UPDATE mpa.users SET failed_attempts=%s,locked_until=%s WHERE id=%s', (fails,until,row['id']))
                return False
            cur.execute('UPDATE mpa.users SET failed_attempts=0,locked_until=NULL WHERE id=%s', (row['id'],))
            _audit(cur, username, 'login', username)
            return True


def change_password(username, old, new):
    if not (12 <= len(new) <= 256) or new == old:
        return False
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT * FROM mpa.users WHERE username=%s FOR UPDATE', (username,))
            user = cur.fetchone()
            if not user or not user['is_active']:
                return False
            try:
                PH.verify(user['password_hash'], old)
            except (VerifyMismatchError, VerificationError):
                return False
            cur.execute('UPDATE mpa.users SET password_hash=%s,must_change_password=false,updated_at=now() WHERE id=%s', (PH.hash(new),user['id']))
            _audit(cur, username, 'password_changed', username)
            return True


def create_user(actor, username, full_name, password, role):
    username = username.strip().lower()
    if not re.fullmatch(r'[a-zA-Z0-9_.-]{3,50}', username):
        raise ValueError('Username: 3–50 λατινικοί χαρακτήρες, αριθμοί, _ . -')
    if not full_name.strip() or not (12 <= len(password) <= 256) or role not in ('admin','analyst'):
        raise ValueError('Απαιτείται όνομα, ρόλος και προσωρινός κωδικός 12–256 χαρακτήρων.')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('INSERT INTO mpa.users (username,display_name,password_hash,role) VALUES (%s,%s,%s,%s)',
                        (username,full_name.strip(),PH.hash(password),role))
            _audit(cur,actor,'user_created',username)


def update_user(actor, username, active, role, temporary_password=None):
    if role not in ('admin','analyst'):
        raise ValueError('Μη έγκυρος ρόλος')
    if temporary_password and not (12 <= len(temporary_password) <= 256):
        raise ValueError('Ο προσωρινός κωδικός χρειάζεται 12–256 χαρακτήρες.')
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Serialize administrator changes, including last-admin protection.
            cur.execute('SELECT pg_advisory_xact_lock(90320261020)')
            cur.execute('SELECT * FROM mpa.users WHERE username=%s FOR UPDATE', (username,))
            target = cur.fetchone()
            if not target:
                raise ValueError('Ο χρήστης δεν υπάρχει')
            if username == actor and (not active or role != 'admin'):
                raise ValueError('Δεν μπορείς να απενεργοποιήσεις ή να υποβαθμίσεις τον δικό σου Admin λογαριασμό.')
            if target['role']=='admin' and (not active or role!='admin'):
                cur.execute("SELECT COUNT(*) FROM mpa.users WHERE role='admin' AND is_active=true")
                if cur.fetchone()['count'] <= 1:
                    raise ValueError('Πρέπει να παραμείνει τουλάχιστον ένας ενεργός Admin.')
            cur.execute('UPDATE mpa.users SET is_active=%s,role=%s,failed_attempts=0,locked_until=NULL,updated_at=now() WHERE id=%s',
                        (active,role,target['id']))
            if temporary_password:
                cur.execute('UPDATE mpa.users SET password_hash=%s,must_change_password=true,updated_at=now() WHERE id=%s',
                            (PH.hash(temporary_password),target['id']))
            _audit(cur,actor,'user_updated',username)


def users_table():
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute('SELECT username,display_name AS full_name,role,is_active AS active,must_change_password AS must_change,created_at FROM mpa.users ORDER BY username')
            return cur.fetchall()


def audit_table():
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""SELECT a.created_at AS at,coalesce(u.username,'system') AS actor,a.action,a.entity_id AS target
                FROM mpa.audit_logs a LEFT JOIN mpa.users u ON a.user_id=u.id
                WHERE a.entity_type='user' ORDER BY a.id DESC LIMIT 100""")
            return cur.fetchall()


def require_login():
    init_auth()
    username = st.session_state.get('auth_username')
    if username:
        user = get_user(username)
        if not user or not user['active'] or time.time()-st.session_state.get('auth_last_seen',0)>SESSION_SECONDS:
            st.session_state.pop('auth_username',None)
            st.session_state.pop('auth_last_seen',None)
        else:
            st.session_state.auth_last_seen = time.time()
            if user['must_change']:
                st.title('🔑 Υποχρεωτική αλλαγή κωδικού')
                st.info('Πριν συνεχίσεις, άλλαξε τον προσωρινό κωδικό σου.')
                with st.form('first_password_change'):
                    old = st.text_input('Προσωρινός κωδικός',type='password')
                    new = st.text_input('Νέος κωδικός (τουλάχιστον 12 χαρακτήρες)',type='password')
                    repeat = st.text_input('Επιβεβαίωση νέου κωδικού',type='password')
                    submitted = st.form_submit_button('Αλλαγή κωδικού')
                if submitted:
                    if new != repeat:
                        st.error('Οι νέοι κωδικοί δεν συμφωνούν.')
                    elif change_password(username,old,new):
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
        password = st.text_input('Password',type='password')
        submitted = st.form_submit_button('Είσοδος')
    if submitted:
        if authenticate(username,password):
            st.session_state.auth_username = username.strip().lower()
            st.session_state.auth_last_seen = time.time()
            st.rerun()
        else:
            st.error('Λανθασμένα στοιχεία ή προσωρινά κλειδωμένος λογαριασμός.')
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM mpa.users')
            if cur.fetchone()[0]==0:
                st.error('Δεν υπάρχει αρχικός Admin. Έλεγξε τα MPA_BOOTSTRAP_ADMIN_* στα Secrets.')
    st.stop()


def admin_screen(current_user):
    if current_user['role']!='admin':
        st.error('Δεν έχεις δικαίωμα διαχείρισης χρηστών.')
        st.stop()
    st.title('👥 Διαχείριση Χρηστών')
    st.dataframe(users_table(),use_container_width=True,hide_index=True)
    with st.expander('➕ Δημιουργία λογαριασμού'):
        with st.form('new_user',clear_on_submit=True):
            username=st.text_input('Username (λατινικοί χαρακτήρες)')
            full_name=st.text_input('Ονοματεπώνυμο')
            role=st.selectbox('Ρόλος',['analyst','admin'])
            password=st.text_input('Προσωρινός κωδικός',type='password')
            submit=st.form_submit_button('Δημιουργία')
        if submit:
            try:
                create_user(current_user['username'],username,full_name,password,role)
                st.success('Ο λογαριασμός δημιουργήθηκε. Απαιτείται αλλαγή κωδικού στην πρώτη είσοδο.')
                st.rerun()
            except errors.UniqueViolation:
                st.error('Το username υπάρχει ήδη.')
            except ValueError as exc:
                st.error(str(exc))
    with st.expander('✏️ Επεξεργασία / επαναφορά κωδικού'):
        options=[u['username'] for u in users_table()]
        if options:
            target_name=st.selectbox('Χρήστης',options)
            target=get_user(target_name)
            with st.form('edit_user'):
                role=st.selectbox('Ρόλος',['analyst','admin'],index=0 if target['role']=='analyst' else 1)
                active=st.checkbox('Ενεργός',value=bool(target['active']))
                password=st.text_input('Νέος προσωρινός κωδικός (προαιρετικά)',type='password')
                submit=st.form_submit_button('Αποθήκευση')
            if submit:
                try:
                    update_user(current_user['username'],target_name,active,role,password or None)
                    st.success('Οι αλλαγές αποθηκεύτηκαν.')
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with st.expander('🕘 Ιστορικό διαχείρισης λογαριασμών'):
        st.dataframe(audit_table(),use_container_width=True,hide_index=True)
