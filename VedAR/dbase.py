import sqlite3
from datetime import datetime


# Database object that controls all the database management
class Database(object):
    def __init__(self):
        # Creates the connection to the database file and the cursor of the connection
        self.conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        self.cur = self.conn.cursor()

    def __del__(self):
        # Saves the changes in the database and close the connection
        self.conn.commit()
        self.cur.close()

    def create_tables(self):
        # Creates the database tables based on the images/database.png diagram
        self.cur.executescript('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(32),
        email VARCHAR(64) UNIQUE,
        password BLOB,
        created_at DATETIME,
        sessions INTEGER DEFAULT 0,
        about TEXT,
        role_id INTEGER,
        institution_id INTEGER );
        
        CREATE TABLE IF NOT EXISTS role (
        id INTEGER NOT NULL PRIMARY KEY,
        name VARCHAR(16) UNIQUE);
        
        CREATE TABLE IF NOT EXISTS institutions (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE);
        
        CREATE TABLE IF NOT EXISTS call (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        start DATETIME);
        
        CREATE TABLE IF NOT EXISTS sessions (
        call_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL );
        
        CREATE TABLE IF NOT EXISTS events (
        call_id INTEGER NOT NULL,
        event TEXT NOT NULL );
        
        CREATE TABLE IF NOT EXISTS friends (
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        PRIMARY KEY(user_id, friend_id) );
        
        CREATE TABLE IF NOT EXISTS messages (
        from_id INTEGER NOT NULL,
        to_id INTEGER NOT NULL,
        message TEXT );
        ''')

    def create_user(self, username, email, role, institution, password):
        # Inserts a new role if it does not exists in the database
        self.cur.execute('INSERT OR IGNORE INTO role (name) VALUES (?)', (role,))
        # Selects the id of the given role name
        role_query = self.cur.execute('SELECT id FROM role WHERE name=?', (role,))
        role_int = role_query.fetchone()[0]

        # Inserts a new institution if it does not exists in the database
        self.cur.execute('INSERT OR IGNORE INTO institutions (name) VALUES (?)', (institution,))
        # Selects the id of the given institution name
        inst_query = self.cur.execute('SELECT id FROM institutions WHERE name=?', (institution,))
        institution_int = inst_query.fetchone()[0]

        # Inserts a new user to the database users table
        self.cur.execute('INSERT INTO users (username, email, password, created_at, role_id, institution_id) VALUES (?,?,?,?,?,?)',
                         (username, email, password, datetime.utcnow(), int(role_int), int(institution_int)))
        # Saves the changes
        self.conn.commit()

    def verify_user(self, email):
        # Select the email and password from the users table given the email (UNIQUE)
        email_query = self.cur.execute('SELECT email, password FROM users WHERE email=?', (email,))
        try:
            # Recover the email and password values
            email_s, password_s = email_query.fetchall()[0]
        except:
            # The email does not exist in the database
            email_s, password_s = None, None

        # Returns the email and password retrieved
        return email_s, password_s

    def search_by_email(self, email):
        # Selects all the information of the users table filtered by email (UNIQUE)
        email_query = self.cur.execute(
            'SELECT users.id, users.username, users.email, DATE(users.created_at), users.sessions, users.about, role.name, institutions.name FROM users JOIN role ON users.role_id=role.id JOIN institutions ON users.institution_id=institutions.id WHERE email=?',
            (email,))

        # Created a new Dictionary with all the information retrieved
        user_data = dict()
        try:
            id_num, username, email, created_at, sessions, about, role, institution = email_query.fetchone()
            user_data['id'] = id_num
            user_data['username'] = username
            user_data['email'] = email
            user_data['created_at'] = created_at
            user_data['sessions'] = sessions
            if about is not None:
                user_data['about'] = about
            user_data['role'] = role
            user_data['institution'] = institution
        except:
            # The user does not exist in the database
            user_data = None

        # Returns the Dictionary with the user data
        return user_data

    def save_changes(self, email, username, institution, role, about):
        # Inserts a new role if it does not exists in the database
        self.cur.execute('INSERT OR IGNORE INTO role (name) VALUES (?)', (role,))
        # Selects the id of the given role name
        role_query = self.cur.execute('SELECT id FROM role WHERE name=?', (role,))
        role_int = role_query.fetchone()[0]

        # Inserts a new institution if it does not exists in the database
        self.cur.execute('INSERT OR IGNORE INTO institutions (name) VALUES (?)', (institution,))
        # Selects the id of the given institution name
        inst_query = self.cur.execute('SELECT id FROM institutions WHERE name=?', (institution,))
        institution_int = inst_query.fetchone()[0]

        # Updates the data of an user given the email (UNIQUE)
        self.cur.execute(
            'UPDATE users SET username=?, about=?, role_id=?, institution_id=? WHERE email=?',
            (username, about, role_int, institution_int, email))

        # Saves the changes
        self.conn.commit()

    def search_friends_by_email(self, email):
        # Select the user id from the users table given the email (UNIQUE)
        email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (email,))

        friends = list()
        try:
            # Recover the user id
            user_id = email_query.fetchone()[0]

            # Recover the list of friend ids
            friends_query = self.cur.execute('SELECT friend_id FROM friends WHERE user_id=?', (user_id,))
            for friend in friends_query.fetchall():
                friend_id = friend[0]
                # For each friend, retrieves the username and email from the users table given the id
                id_query = self.cur.execute('SELECT username, email FROM users WHERE id=?', (friend_id,))
                friend_username, friend_email = id_query.fetchone()
                # Appends the Dictionary with the data to the friends List
                friends.append({
                    'username': friend_username,
                    'email': friend_email,
                })
        except Exception as e:
            print('ERROR SEARCHING FRIENDS')

        # Return the List of friends
        return friends

    def add_friend(self, email, friend_email):
        # Select the user id from the users table given the email (UNIQUE)
        email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (email,))

        errors = dict()
        try:
            # Recover the user id
            user_id = email_query.fetchone()[0]

            try:
                # Recover the friend id
                friend_email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (friend_email,))
                friend_id = friend_email_query.fetchone()[0]

                # Recover the list of friend ids
                friends_query = self.cur.execute('SELECT friend_id FROM friends WHERE user_id=?', (user_id,))
                friend_ids = friends_query.fetchall()
                # Verifies if the friend is already in the user friend list
                for fr in friend_ids:
                    if friend_id in fr:
                        errors['already_exists'] = 'Ya ha agregado a ese usuario como amigo'
                    else:
                        continue

                # Verifies if both ids are the same
                if friend_id == user_id:
                    errors['same'] = 'Usted mismo no se puede agregar como amigo'

                if not errors:
                    # Add the friend and user id into the friends table
                    self.cur.execute('INSERT INTO friends (user_id, friend_id) VALUES (?, ?)',
                                     (user_id, friend_id))
                    # Saves the changes
                    self.conn.commit()
            except:
                errors['no_exists'] = 'El usuario buscado no existe'
        except:
            print('ERROR ADDING FRIEND')

        # Return any errors generated
        return errors

    def send_message(self, email, friend_email, message):
        # Select the user id from the users table given the email (UNIQUE)
        email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (email,))

        errors = dict()
        try:
            # Recover the user id
            user_id = email_query.fetchone()[0]

            try:
                # Recover the friend id
                email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (friend_email,))
                friend_id = email_query.fetchone()[0]

                # Verifies if both ids are the same
                if friend_id == user_id:
                    errors['same'] = 'Usted mismo no se puede enviar un mensaje'

                if not errors:
                    # Add the friend id, user id, and message into the messages table
                    self.cur.execute('INSERT INTO messages (from_id, to_id, message) VALUES (?, ?, ?)',
                                     (user_id, friend_id, message))
                    # Saves the changes
                    self.conn.commit()
            except:
                errors['no_exists'] = 'El usuario buscado no existe'
        except:
            print('ERROR SENDING MESSAGE')

        return errors

    def recover_messages(self, email):
        # Select the user id from the users table given the email (UNIQUE)
        email_query = self.cur.execute('SELECT id FROM users WHERE email=?', (email,))

        messages = list()
        try:
            user_id = email_query.fetchone()[0]
            message_query = self.cur.execute('SELECT from_id, message FROM messages WHERE to_id=?', (user_id,))

            for message in message_query.fetchall():
                from_query = self.cur.execute('SELECT username, email FROM users WHERE id=?', (message[0],))
                username, from_email = from_query.fetchone()
                messages.append({
                    'username': username,
                    'email': from_email,
                    'message': message[1]
                })
        except:
            print('ERROR RETRIEVING MESSAGES')

        # Return any errors generated
        return messages

    def add_session(self, email):
        # Generate the actual date
        actual_time = datetime.utcnow()
        # Adds a new call to the call table
        self.cur.execute('INSERT INTO call (start) VALUES (?)', (actual_time,))

        # Select the id from the recently added call
        call_query = self.cur.execute('SELECT id FROM call WHERE start=?', (actual_time,))
        call_id = call_query.fetchone()[0]

        # Select the user id from the users table given the email (UNIQUE)
        user_query = self.cur.execute('SELECT id FROM users WHERE email=?', (email,))
        user_id = user_query.fetchone()[0]

        # Adds a new session with the corresponding call and user id
        self.cur.execute('INSERT INTO sessions (call_id, user_id) VALUES (?, ?)', (call_id, user_id))

        # Adds one to the session count of the user
        self.cur.execute('UPDATE users SET sessions = sessions + 1 WHERE email=?', (email,))

        # Saves the changes
        self.conn.commit()
