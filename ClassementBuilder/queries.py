def get_query_create(table_name: str, month: str):
        return f"""CREATE TABLE IF NOT EXISTS {table_name}__{month} (
                id INT,
                ranking INT,
        
                PRIMARY KEY (id)
                );"""