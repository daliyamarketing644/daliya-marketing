import os
from flask import Flask, render_template, request, redirect, url_for, session, abort, Response
import sqlite3
import csv
import math
from dotenv import load_dotenv
from io import TextIOWrapper
from functools import wraps
load_dotenv()

app = Flask(__name__)
# പ്രൊഫഷണൽ ആപ്പുകളിൽ സെക്രെട്ട് കീ സുരക്ഷിതമായി സൂക്ഷിക്കുക
app.secret_key = os.getenv('FLASK_SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USER')
ADMIN_PASSWORD = os.getenv('ADMIN_PASS')

def get_db_connection():
    conn = sqlite3.connect('daliya.db')
    conn.row_factory = sqlite3.Row
    return conn

# 🔐 അഡ്മിൻ സെക്യൂരിറ്റിക്ക് വേണ്ടിയുള്ള ഡെക്കറേറ്റർ (ക്ലീൻ കോഡ് ശൈലി)
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- USER HOMEPAGE ---
@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    total_products = conn.execute('SELECT COUNT(*) FROM products WHERE is_available = 1').fetchone()[0]
    
    products = conn.execute('''
        SELECT * FROM products 
        WHERE is_available = 1
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    brands = conn.execute('SELECT * FROM brands WHERE is_available = 1').fetchall()
    conn.close()

    total_pages = math.ceil(total_products / per_page)

    return render_template('index.html', 
                           products=products, 
                           brands=brands, 
                           current_page=page, 
                           total_pages=total_pages)

# --- BRAND DETAILS PAGE ---
@app.route('/brand/<brand_id>')
def brand_details(brand_id):
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    brand = conn.execute('SELECT * FROM brands WHERE brand_id = ? AND is_available = 1', (brand_id,)).fetchone()
    
    if brand is None:
        conn.close()
        return "Brand not found or currently unavailable", 404

    total_products = conn.execute('SELECT COUNT(*) FROM products WHERE brand_id = ? AND is_available = 1', (brand_id,)).fetchone()[0]
    
    products = conn.execute('''
        SELECT * FROM products 
        WHERE brand_id = ? AND is_available = 1
        LIMIT ? OFFSET ?
    ''', (brand_id, per_page, offset)).fetchall()
    
    brands = conn.execute('SELECT * FROM brands WHERE is_available = 1').fetchall()
    conn.close()

    total_pages = math.ceil(total_products / per_page)

    return render_template('brand_details.html', 
                           brand=brand, 
                           products=products, 
                           brands=brands,
                           current_page=page, 
                           total_pages=total_pages)

# --- ADMIN PANEL LOGIN ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if 'logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid Username or Password!'
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))


# --- 1. ADMIN BRAND MANAGEMENT ---
@app.route('/admin/brand')
@admin_required
def admin_brand_page():
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    conn.close()
    return render_template('admin_brand.html', brands=brands)

@app.route('/admin/add_brand', methods=['POST'])
@admin_required
def add_brand():
    brand_id = request.form['brand_id'].strip().lower()
    brand_name = request.form['brand_name'].strip()
    if brand_id and brand_name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO brands (brand_id, brand_name, is_available) VALUES (?, ?, 1)', (brand_id, brand_name))
            conn.commit()
        except sqlite3.IntegrityError: 
            pass
        conn.close()
    return redirect(url_for('admin_brand_page'))

@app.route('/admin/edit_brand/<brand_id>', methods=['POST'])
@admin_required
def edit_brand(brand_id):
    new_name = request.form['brand_name'].strip()
    if new_name:
        conn = get_db_connection()
        conn.execute('UPDATE brands SET brand_name = ? WHERE brand_id = ?', (new_name, brand_id))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_brand_page'))

@app.route('/admin/delete_brand/<brand_id>')
@admin_required
def delete_brand(brand_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE brand_id = ?', (brand_id,))
    conn.execute('DELETE FROM brands WHERE brand_id = ?', (brand_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_brand_page'))


# --- 2. ADMIN PRODUCT MANAGEMENT ---
@app.route('/admin/product')
@admin_required
def admin_product_page():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    
    products = conn.execute('''
        SELECT products.*, brands.brand_name 
        FROM products 
        JOIN brands ON products.brand_id = brands.brand_id
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    conn.close()
    
    total_pages = math.ceil(total_products / per_page)
    
    return render_template('admin_product.html', 
                           brands=brands, 
                           products=products,
                           current_page=page, 
                           total_pages=total_pages)

@app.route('/admin/add_product', methods=['POST'])
@admin_required
def add_product():
    brand_id = request.form['brand_id']
    name = request.form['name'].strip()
    packing = request.form['packing'].strip()
    mrp = request.form['mrp'].strip()
    img = request.form['img'].strip()
    if brand_id and name and packing and mrp:
        if not img: img = 'product.png'
        conn = get_db_connection()
        conn.execute('INSERT INTO products (brand_id, name, packing, mrp, img, is_available) VALUES (?, ?, ?, ?, ?, 1)',
                     (brand_id, name, packing, mrp, img))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_product_page'))

@app.route('/admin/edit_product/<int:id>', methods=['POST'])
@admin_required
def edit_product(id):
    name = request.form['name'].strip()
    packing = request.form['packing'].strip()
    mrp = request.form['mrp'].strip()
    img = request.form['img'].strip()
    
    if name and packing and mrp:
        conn = get_db_connection()
        conn.execute('UPDATE products SET name=?, packing=?, mrp=?, img=? WHERE id=?', 
                     (name, packing, mrp, img, id))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_product_page'))

@app.route('/admin/delete_product/<int:id>')
@admin_required
def delete_product(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_product_page'))


# --- CSV BULK UPLOAD FUNCTIONS ---
@app.route('/admin/upload_brands', methods=['POST'])
@admin_required
def upload_brands():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    if file and file.filename.endswith('.csv'):
        csv_file = TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.reader(csv_file)
        next(csv_reader) # Header skip ചെയ്യാൻ
        
        conn = get_db_connection()
        for row in csv_reader:
            if len(row) >= 2:
                brand_id = row[0].strip().lower()
                brand_name = row[1].strip()
                try:
                    conn.execute('INSERT OR IGNORE INTO brands (brand_id, brand_name, is_available) VALUES (?, ?, 1)', (brand_id, brand_name))
                except Exception as e:
                    print(f"Error inserting brand: {e}")
        conn.commit()
        conn.close()
        return redirect(url_for('admin_brand_page'))
    
    return "Invalid file format. Please upload a CSV file.", 400

@app.route('/admin/upload_products', methods=['POST'])
@admin_required
def upload_products():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    if file and file.filename.endswith('.csv'):
        csv_file = TextIOWrapper(file.stream, encoding='utf-8')
        csv_reader = csv.reader(csv_file)
        next(csv_reader)
        
        conn = get_db_connection()
        for row in csv_reader:
            if len(row) >= 4:
                brand_id = row[0].strip().lower()
                name = row[1].strip()
                packing = row[2].strip()
                mrp = row[3].strip()
                img = row[4].strip() if len(row) > 4 and row[4].strip() else "product.png"
                
                try:
                    # ഇവിടെ is_available = 1 എന്ന് നേരിട്ട് ഉറപ്പുവരുത്തുന്നു
                    conn.execute('''
                        INSERT INTO products (brand_id, name, packing, mrp, img, is_available) 
                        VALUES (?, ?, ?, ?, ?, 1)
                    ''', (brand_id, name, packing, mrp, img))
                except Exception as e:
                    print(f"Error inserting product: {e}")
        conn.commit()
        conn.close()
        return redirect(url_for('admin_product_page'))
    
    return "Invalid file format. Please upload a CSV file.", 400


# --- CSV TEMPLATE DOWNLOADS ---
@app.route('/admin/download_brand_template')
@admin_required
def download_brand_template():
    csv_data = "brand_id,brand_name\nnestle,Nestle\nmilma,Milma\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=brand_template.csv"}
    )

@app.route('/admin/download_product_template')
@admin_required
def download_product_template():
    csv_data = "brand_id,name,packing,mrp,img\nnestle,KitKat 45g,1 Pack,30,kitkat.png\nmilma,Milma Peda 250g,1 Box,150,milma_peda.png\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=product_template.csv"}
    )

# --- BRAND TOGGLE STATUS (HIDE / SHOW) ---
@app.route('/admin/toggle_brand/<brand_id>')
@admin_required
def toggle_brand(brand_id):
    conn = get_db_connection()
    current = conn.execute('SELECT is_available FROM brands WHERE brand_id = ?', (brand_id,)).fetchone()
    if current:
        new_status = 0 if current['is_available'] == 1 else 1
        conn.execute('UPDATE brands SET is_available = ? WHERE brand_id = ?', (new_status, brand_id))
        conn.execute('UPDATE products SET is_available = ? WHERE brand_id = ?', (new_status, brand_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_brand_page'))


# --- PRODUCT TOGGLE STATUS (HIDE / SHOW) ---
@app.route('/admin/toggle_product/<int:id>')
@admin_required
def toggle_product(id):
    conn = get_db_connection()
    current = conn.execute('SELECT is_available FROM products WHERE id = ?', (id,)).fetchone()
    if current:
        new_status = 0 if current['is_available'] == 1 else 1
        conn.execute('UPDATE products SET is_available = ? WHERE id = ?', (new_status, id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_product_page'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)