import uvicorn
from fastapi import FastAPI, Request, Response, Form, HTTPException
from fastapi.responses import HTMLResponse
import json
from jinja2 import Environment, FileSystemLoader
from pymysql import cursors, connect
import sys
import subprocess



app = FastAPI()
templates = Environment(loader=FileSystemLoader('templates'))


def in_db(db, its):
    found = []
    for i in its:
        if i in db:
            found.append(i)
        else:
            pass
    return found

@app.get("/", response_class=HTMLResponse)
def read_root():
    return templates.get_template('index.html').render()

@app.get("/users", response_class=HTMLResponse)
def read_root():
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    result = []
    with connection:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `Users_Master_TAB`"
            cursor.execute(sql)
            result = cursor.fetchall()
                
    return templates.get_template('users.html').render({'users': result})

@app.get("/products", response_class=HTMLResponse)
def read_root():
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `Product_Master_TAB`"
        cursor.execute(sql)
        result = cursor.fetchall()
    return templates.get_template('products.html').render({"items": result})

@app.get("/cart", response_class=HTMLResponse)
def read_root():
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `Cart_TAB`"
        cursor.execute(sql)
        result = cursor.fetchall()
        
    return templates.get_template('user_cart.html').render({"carts": result})

@app.get("/purchases", response_class=HTMLResponse)
def read_root():
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `Purchase_TAB`"
        cursor.execute(sql)
        result = cursor.fetchall()
        
    return templates.get_template('user_purchases.html').render({'purchases': result})

@app.post("/users/add", response_class=HTMLResponse)
def add_user(name: str = Form(...), email: str = Form(...), password: str = Form(...)):
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    with connection.cursor() as cursor:
        sql = f"INSERT INTO `Users_Master_TAB` (`name`, `email`, `password`) VALUES ('{name}','{email}','{password}')"
        cursor.execute(sql)
    connection.commit()
    
    with connection.cursor() as cursor:
        sql = f"SELECT `id` FROM `Users_Master_TAB` WHERE `email`='{email}'"
        cursor.execute(sql)
    
        c_sql = "INSERT INTO `Cart_TAB`(`customer_id`, `items`) VALUES (%s,%s)"
        cursor.execute(c_sql, (int(cursor.fetchone()['id']), json.dumps({"items": []})))
    connection.commit()


    return templates.get_template('redirect.html').render({'url': '/users'})

@app.post("/cart/add", response_class=HTMLResponse)
def add_cart(user_key: int = Form(...), item_id: str = Form(...), quantity: str = Form(...)):
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    query = f"SELECT`items` FROM `Cart_TAB` WHERE `customer_id`={user_key}"
    #j_value = {'id': int(item_id), 'quantity': int(quantity)}
    n_q = "UPDATE `Cart_TAB` SET `customer_id`=%s,`items`=%s WHERE `customer_id`=%s"
    
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        r = cursor.fetchone()
        r = json.loads(r['items'])
        r['items'].append({'item_id': int(item_id), 'quantity': int(quantity)})

        cursor.execute(n_q, (user_key, json.dumps(r), user_key))
    
    connection.commit()
    return templates.get_template('redirect.html').render({'url': '/cart'})

@app.post("/products/add", response_class=HTMLResponse)
def add_product(name: str = Form(...), price: str = Form(...), img_url: str = Form(...), type: str = Form(...), brand: str = Form(...)):
    query = "INSERT INTO `Product_Master_TAB`(`name`, `price`, `img_url`, `type`, `brand`) VALUES (%s,%s,%s,%s,%s)"

    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    
    with connection.cursor() as cursor:
        cursor.execute(query,(str(name), float(price), str(img_url), str(type), str(brand)))
    connection.commit()
    return templates.get_template('redirect.html').render({'url': '/products'})

@app.post("/purchases/add", response_class=HTMLResponse)
def add_purchase(customer_id: int = Form(...), items: str = Form(...)):
    items.replace('\r', '')
    it = items.split('\n')
    items = [i.split(',') for i in it]
    
    ids = [int(i[0]) for i in items]
    quantities = [int(i[1]) for i in items]
    db_ids = []
    
    connection = connect(host='localhost',
                             user='root',
                             password='root',
                             database='MAIN_DB',
                             cursorclass=cursors.DictCursor)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT `p_id` FROM `Product_Master_TAB`;")
        for i in cursor.fetchall():
            db_ids.append(int(i['p_id']))
            
        hits = in_db(db_ids, ids)   
        schma = {'items': []}
        for hit in hits:
            jj = {'id': hit, 'quantity': quantities[ids.index(hit)]}
            schma['items'].append(jj)
        
        sql = "INSERT INTO `Purchase_TAB`(`customer_id`,`items`) VALUES (%s,%s)"
        cursor.execute(sql, (customer_id, json.dumps(schma)))
            
    connection.commit()

    return templates.get_template('redirect.html').render({'url': '/purchases'})

if __name__ == "__main__":
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r','requirements.txt'])
    except subprocess.CalledProcessError:
        pass
    
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)