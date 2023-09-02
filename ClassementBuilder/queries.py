def get_query_create(table_name: str, month: str):
        return f"""CREATE TABLE IF NOT EXISTS {table_name}__{month} (
                id INT,
                username VARCHAR(256),
                username_upper VARCHAR(256),

                points REAL,
                ranking INT,
        
                PRIMARY KEY (id)
                );"""