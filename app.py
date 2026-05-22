from flask import Flask, render_template, request, redirect, url_for, session, abort, Response
import sqlite3
import csv
import math
from io import TextIOWrapper

app = Flask(__name__)
app.secret_key = 'daliya_marketing_secret_key'

def get_db_connection():
    conn = sqlite3.connect('daliya.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- USER HOMEPAGE (WITH PAGINATION) ---
@app.route('/')
def home():
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    
    # kevalam available aaya products mathram count cheyyunnu
    total_products = conn.execute('SELECT COUNT(*) FROM products WHERE is_available = 1').fetchone()[0]
    
    products = conn.execute('''
        SELECT * FROM products 
        WHERE is_available = 1
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    # kevalam available aaya brands mathram home-il kaanikkunnu
    brands = conn.execute('SELECT * FROM brands WHERE is_available = 1').fetchall()
    conn.close()

    total_pages = math.ceil(total_products / per_page)

    return render_template('index.html', 
                           products=products, 
                           brands=brands, 
                           current_page=page, 
                           total_pages=total_pages)

# --- BRAND DETAILS PAGE (FIXED INTERNAL SERVER ERROR) ---
@app.route('/brand/<brand_id>')
def brand_details(brand_id):
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    
    # Brand available aano ennu koodi check cheyyunnu
    brand = conn.execute('SELECT * FROM brands WHERE brand_id = ? AND is_available = 1', (brand_id,)).fetchone()
    
    if brand is None:
        conn.close()
        return "Brand not found or currently unavailable", 404

    # ee brand-il available aaya products mathram count cheyyunnu
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
        if username == 'admin' and password == 'daliya123':
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid Username or Password!'
    return render_template('admin_login.html', error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))


# --- 1. ADMIN BRAND MANAGEMENT ---
@app.route('/admin/brand')
def admin_brand_page():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    conn.close()
    return render_template('admin_brand.html', brands=brands)

@app.route('/admin/add_brand', methods=['POST'])
def add_brand():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    brand_id = request.form['brand_id'].strip().lower()
    brand_name = request.form['brand_name'].strip()
    if brand_id and brand_name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO brands (brand_id, brand_name) VALUES (?, ?)', (brand_id, brand_name))
            conn.commit()
        except sqlite3.IntegrityError: pass
        conn.close()
    return redirect(url_for('admin_brand_page'))

@app.route('/admin/edit_brand/<brand_id>', methods=['POST'])
def edit_brand(brand_id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    new_name = request.form['brand_name'].strip()
    if new_name:
        conn = get_db_connection()
        conn.execute('UPDATE brands SET brand_name = ? WHERE brand_id = ?', (new_name, brand_id))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_brand_page'))

@app.route('/admin/delete_brand/<brand_id>')
def delete_brand(brand_id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE brand_id = ?', (brand_id,))
    conn.execute('DELETE FROM brands WHERE brand_id = ?', (brand_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_brand_page'))


# --- 2. ADMIN PRODUCT MANAGEMENT (ADDED PAGINATION & FIXED REDIRECTS) ---
@app.route('/admin/product')
def admin_product_page():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    
    # ആകെ പ്രൊഡക്റ്റുകളുടെ എണ്ണം
    total_products = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    
    # ആവശ്യമായ 50 പ്രൊഡക്റ്റുകൾ മാത്രം JOIN വഴി എടുക്കുന്നു
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
def add_product():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    brand_id = request.form['brand_id']
    name = request.form['name'].strip()
    packing = request.form['packing'].strip()
    mrp = request.form['mrp'].strip()
    img = request.form['img'].strip()
    if brand_id and name and packing and mrp:
        if not img: img = 'product.png'
        conn = get_db_connection()
        conn.execute('INSERT INTO products (brand_id, name, packing, mrp, img) VALUES (?, ?, ?, ?, ?)',
                     (brand_id, name, packing, mrp, img))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_product_page'))

@app.route('/admin/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
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
def delete_product(id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_product_page'))


# --- CSV BULK UPLOAD FUNCTIONS ---
@app.route('/admin/upload_brands', methods=['POST'])
def upload_brands():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
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
            if len(row) >= 2:
                brand_id = row[0].strip().lower()
                brand_name = row[1].strip()
                try:
                    conn.execute('INSERT OR IGNORE INTO brands (brand_id, brand_name) VALUES (?, ?)', (brand_id, brand_name))
                except Exception as e:
                    print(f"Error inserting brand: {e}")
        conn.commit()
        conn.close()
        return redirect(url_for('admin_brand_page'))
    
    return "Invalid file format. Please upload a CSV file.", 400

@app.route('/admin/upload_products', methods=['POST'])
def upload_products():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
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
                img = row[4].strip() if len(row) > 4 else "product.png"
                
                try:
                    conn.execute('''
                        INSERT INTO products (brand_id, name, packing, mrp, img) 
                        VALUES (?, ?, ?, ?, ?)
                    ''', (brand_id, name, packing, mrp, img))
                except Exception as e:
                    print(f"Error inserting product: {e}")
        conn.commit()
        conn.close()
        return redirect(url_for('admin_product_page'))
    
    return "Invalid file format. Please upload a CSV file.", 400


# --- CSV TEMPLATE DOWNLOADS ---
@app.route('/admin/download_brand_template')
def download_brand_template():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    csv_data = "brand_id,brand_name\nnestle,Nestle\nmilma,Milma\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=brand_template.csv"}
    )

@app.route('/admin/download_product_template')
def download_product_template():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    csv_data = "brand_id,name,packing,mrp,img\nnestle,KitKat 45g,1 Pack,30,kitkat.png\nmilma,Milma Peda 250g,1 Box,150,milma_peda.png\n"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=product_template.csv"}
    )

# --- BRAND TOGGLE STATUS (HIDE / SHOW) ---
@app.route('/admin/toggle_brand/<brand_id>')
def toggle_brand(brand_id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    # Nilvile status nokkunnu
    current = conn.execute('SELECT is_available FROM brands WHERE brand_id = ?', (brand_id,)).fetchone()
    if current:
        # 1 aayirunnengil 0 aakkunnu, 0 aayirunnengil 1 aakkunnu
        new_status = 0 if current['is_available'] == 1 else 1
        conn.execute('UPDATE brands SET is_available = ? WHERE brand_id = ?', (new_status, brand_id))
        # Oru brand hide cheydhal athile ella products-um taniye hide aavan (Optional)
        conn.execute('UPDATE products SET is_available = ? WHERE brand_id = ?', (new_status, brand_id))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_brand_page'))


# --- PRODUCT TOGGLE STATUS (HIDE / SHOW) ---
@app.route('/admin/toggle_product/<int:id>')
def toggle_product(id):
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
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
    return render_template('about.html') # ഫയലിന്റെ പേര്

@app.route('/services')
def services():
    return render_template('services.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)