from collections import defaultdict
import pandas as pd
from database_scripts.create_connection import create_db_connection
from database_scripts.three_nf import item_from_db

"""Functions here do moderate to intense transformation of data.
They use raw data from dataframe or send SELECT queries to database for data needed.
Data transitions between dataframe, dictionaries, and a list of tuples,
the final format needed by the execute_values of psycopg2 in insert_data.py file"""

connection = create_db_connection()

def chunk(lst, n): #chunks a list in multiples of n integer
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def transform(df): #This returned hashed name
    col = 'order'
    df[col] = df[col].str.split(',')
    df[col] = df[col].apply(lambda x: chunk(x, 1))  #split in 3's
    return df


def convert_order_to_dict(df): #converts order DF to python dict
    dic = defaultdict()
    col = 'order'
    for i, _ in enumerate(df[col]):
        try:
            dic[df['customer_hash'].iloc[i]] += df[col].iloc[i]
        except KeyError:
            dic[df['customer_hash'].iloc[i]] = df[col].iloc[i]
            
    new_dic = defaultdict()
    for k, v in dic.items():
        new_dic[k] = [in_lst.rsplit('-', 1) for out_lst in v for in_lst in out_lst]
    return new_dic

def convert_to_DF(dic): #converts back to DF
    dic_list = [(key, *i) for key,value in dic.items() for i in value] #converts dict to list of tuples
    df = pd.DataFrame(dic_list, columns=['customer_hash','Orders','Price'])
    df['Orders'] = df['Orders'].str.strip()
    df['Price'] = df['Price'].astype(float)
    return df
    
def convert_3NF_items_for_db(df, col): #converts from DF to python list
    lst = []
    for i, _ in enumerate(df[col]):
        lst.append(df[col].iloc[i])
    return lst

def convert_df_to_dict(data): #Converts any DF to list of tuples needed by psycopg2 execute_values
    arr = data.values
    df = [tuple(i) for i in arr]
    return df

def group_product(data6, connection, table, item):
    df = data6.groupby(['Orders', 'Price']).size().reset_index(name='total_quantity')
    df_item = item_from_db(connection, table, item)
    df_item.columns = ['Orders', 'Price']
    df.columns = ['Orders', 'Price', 'total_quantity']
    df.drop(columns ='total_quantity', inplace=True)
    df['Orders'] = df['Orders'].str.strip()
    df_item['Orders'] = df_item['Orders'].str.strip()
    if df_item.empty:
        set_df = df
    else:
        set_df = pd.concat([df,df_item]).drop_duplicates(subset=['Orders'],keep=False)
    print(df_item)
    return set_df

def get_customer_from_db(connection):
    try:
        query_customer = pd.read_sql_query(
        """select *
        from customers""", connection)

        df_customer = pd.DataFrame(query_customer, columns=['customer_id', 'customer_hash'])
        return df_customer
    except Exception as e:
        print(e)

def get_location_from_db(connection):
    try:
        query_location = pd.read_sql_query(
        """select *
        from locations""", connection)

        df_location = pd.DataFrame(query_location, columns=['location_id', 'location'])
        return df_location
    except Exception as e:
        print(e)
        
def get_payment_from_db(connection):
    try:
        query_payment = pd.read_sql_query(
        """select *
        from payments""", connection)

        df_payment = pd.DataFrame(query_payment, columns=['payment_id', 'payment_type'])
        return df_payment
    except Exception as e:
        print(e)
        
def get_product_from_db(connection):
    try:
        query_product = pd.read_sql_query(
        """select *
        from products""", connection)

        df_product = pd.DataFrame(query_product, columns=['product_id', 'product_name', 'product_price'])
        df_product.rename(columns={'product_name':'Orders'}, inplace = True)
        return df_product
    except Exception as e:
        print(e)

def get_order_id_from_db(connection):
    try:
        query_order = pd.read_sql_query(
        """select o.order_id, c.customer_id, c.customer_hash
        from orders o
        join customers c
        on o.customer_id = c.customer_id""", connection)

        df_order = pd.DataFrame(query_order, columns=['order_id', 'customer_id', 'customer_hash'])
        return df_order
    except Exception as e:
        print(e)