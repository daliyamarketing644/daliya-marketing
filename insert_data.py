import sqlite3

def add_product(brand_id, name, packing, mrp, img):
    conn = sqlite3.connect('daliya.db')
    cursor = conn.cursor()
    
    # പുതിയ പ്രൊഡക്റ്റ് ഇൻസേർട്ട് ചെയ്യാനുള്ള SQL Query
    try:
        cursor.execute('''
            INSERT INTO products (brand_id, name, packing, mrp, img)
            VALUES (?, ?, ?, ?, ?)
        ''', (brand_id, name, packing, mrp, img))
        
        conn.commit()
        print(f"Success: {name} വിജയകരമായി ചേർത്തു!")
    except Exception as e:
        print(f"Error: ഡാറ്റ ചേർക്കാൻ പറ്റിയില്ല. കസ്റ്റം എറർ: {e}")
    finally:
        conn.close()

# --- ഇവിടെ നിങ്ങൾക്ക് പുതിയ പ്രൊഡക്റ്റുകൾ നൽകാം ---
# ഫങ്ക്ഷൻ ഫോർമാറ്റ്: add_product('brand_id', 'Product Name', 'Packing', 'MRP', 'image_name.png')

add_product('milma', 'Milma Peda', '250 g', '140.00', 'milma_peda.png')
add_product('kopiko', 'Kopiko Candy Big Jar', '1 kg', '350.00', 'kopiko_jar.png')
add_product('suraj_ada', 'Suraj Payasam Mix', '400 g', '90.00', 'suraj_payasam.jpg')