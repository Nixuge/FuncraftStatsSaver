from typing_extensions import override


class QueriesThreads:
    @staticmethod
    def get_create_repo_table_query(name: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                thread_id INT,
                pages INT,

                prefixe VARCHAR(256),
                titre VARCHAR(1024),

                reponses INT,
                affichages INT,

                autheur_nom VARCHAR(256),
                autheur_id INT,

                date_creation VARCHAR(256),

                sticky BOOL,

                full_url VARCHAR(1024),

                PRIMARY KEY (thread_id)
                );"""
    
    @staticmethod
    def get_insert_query(name: str) -> str:
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?,?,?);"""
    
    @staticmethod
    def get_where_contains_key(table: str, column: str, value: str):
        return f"""SELECT * FROM {table} WHERE {column}=\"{value}\""""
    
    @classmethod
    def get_where_contains_thread_id(cls, name: str, thread_id: str):
        return cls.get_where_contains_key(name, "thread_id", thread_id)


class QueriesPosts:
    # Note: le sondage est super inneficace, y'a besoin de le stocker 1x par thread
    # et la ça le save pr CHAQUE POST dans le thread,
    # mais pas le temps je traiterai plus tard si y faut honnetement
    @staticmethod
    def get_create_repo_table_query(name: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                post_id INT,
                parent_thread_id INT,

                post_number INT,
                post_author_id INT,
                post_author_name VARCHAR(256),

                edit_date VARCHAR(256),
                post_date VARCHAR(256),

                likes BLOB,

                post_content BLOB,

                sondage BLOB,

                PRIMARY KEY (post_id)
                );"""
    
    @staticmethod
    def get_insert_query(name: str) -> str:
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?,?);"""
    
    @staticmethod
    def get_where_contains_key(table: str, column: str, value: str):
        return f"""SELECT * FROM {table} WHERE {column}=\"{value}\""""
    
    @classmethod
    def get_where_contains_post_id(cls, name: str, post_id: str):
        return cls.get_where_contains_key(name, "post_id", post_id)


# TODO AFTER: USERS DB