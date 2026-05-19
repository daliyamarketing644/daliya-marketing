from flask import Flask, render_template, request, redirect, url_for, session, abort
import sqlite3

app = Flask(__name__)
app.secret_key = 'daliya_marketing_secret_key'

def get_db_connection():
    conn = sqlite3.connect('daliya.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    conn.close()
    return render_template('index.html', brands=brands)

@app.route('/brand/<brand_id>')
def brand_details(brand_id):
    conn = get_db_connection()
    brand = conn.execute('SELECT * FROM brands WHERE brand_id = ?', (brand_id,)).fetchone()
    if brand is None:
        conn.close()
        abort(404)
    products = conn.execute('SELECT * FROM products WHERE brand_id = ?', (brand_id,)).fetchall()
    conn.close()
    return render_template('brand_details.html', brand=brand, products=products)

# --- ADMIN PANEL LOGGING ---

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
    # ബ്രാൻഡ് ഡിലീറ്റ് ചെയ്യുമ്പോൾ അതിലെ പ്രൊഡക്റ്റുകളും ഡിലീറ്റ് ചെയ്യാം
    conn.execute('DELETE FROM products WHERE brand_id = ?', (brand_id,))
    conn.execute('DELETE FROM brands WHERE brand_id = ?', (brand_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_brand_page'))


# --- 2. ADMIN PRODUCT MANAGEMENT ---

@app.route('/admin/product')
def admin_product_page():
    if 'logged_in' not in session: return redirect(url_for('admin_login'))
    conn = get_db_connection()
    brands = conn.execute('SELECT * FROM brands').fetchall()
    # ഇവിടെ ബ്രാൻഡിന്റെ പേര് കൂടി കിട്ടാൻ JOIN ക്വറി ഉപയോഗിക്കുന്നു
    products = conn.execute('''
        SELECT products.*, brands.brand_name 
        FROM products 
        JOIN brands ON products.brand_id = brands.brand_id
    ''').fetchall()
    conn.close()
    return render_template('admin_product.html', brands=brands, products=products)

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

if __name__ == '__main__':
    app.run(debug=True)