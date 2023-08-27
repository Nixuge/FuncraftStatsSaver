from typing_extensions import override


class Queries:
    @staticmethod
    def get_create_repo_table_query(name: str) -> str:
        # username as varchar 256 just to be sure, doesn't use much more anyways
        # same for inscription/derniere_connexion

        # glore_total & parties_jouees prolly in the gzipped stats too but meh
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                id INT,
                username VARCHAR(256),

                rank VARCHAR(256),

                inscription VARCHAR(256),
                derniere_connexion VARCHAR(256),

                gloires_total INT,
                parties_jouees INT,

                gzipped_stats BLOB,
                gzipped_friends BLOB,

                image_id VARCHAR(40),
                image BLOB,    
        
                PRIMARY KEY (id)
                );"""
    
    @staticmethod
    def get_insert_query() -> str:
        return f"""INSERT INTO funcraft_stats VALUES (?,?,?,?,?,?,?,?,?,?,?);"""
    
    @staticmethod
    def get_where_contains_key(table: str, column: str, value: str):
        return f"""SELECT * FROM {table} WHERE {column}=\"{value}\""""
    
    @staticmethod
    def get_where_contains_id(id: str):
        return Queries.get_where_contains_key("funcraft_stats", "id", id)
