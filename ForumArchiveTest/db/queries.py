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
    @staticmethod
    def get_create_repo_table_query(name: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                post_id INT,
                parent_thread_id INT,

                post_number INT,
                post_author_id INT,

                edit_date VARCHAR(256),
                post_date VARCHAR(256),

                likes BLOB,

                post_content BLOB,

                PRIMARY KEY (post_id)
                );"""
    
    @staticmethod
    def get_insert_query(name: str) -> str:
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?);"""
    
    @staticmethod
    def get_where_contains_key(table: str, column: str, value: str):
        return f"""SELECT * FROM {table} WHERE {column}=\"{value}\""""
    
    @classmethod
    def get_where_contains_post_id(cls, name: str, post_id: str):
        return cls.get_where_contains_key(name, "post_id", post_id)


# TODO AFTER: USERS DB