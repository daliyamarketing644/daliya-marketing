import sqlite3

# daliya.db എന്ന പേരിൽ ഒരു ഡാറ്റാബേസ് ഫയൽ ഉണ്ടാക്കുന്നു
conn = sqlite3.connect('daliya.db')
cursor = conn.cursor()

# 1. ബ്രാൻഡുകൾക്ക് വേണ്ടിയുള്ള ടേബിൾ (Brands Table)
cursor.execute('''
CREATE TABLE IF NOT EXISTS brands (
    brand_id TEXT PRIMARY KEY,
    brand_name TEXT NOT NULL
)
''')

# 2. ഉൽപ്പന്നങ്ങൾക്ക് വേണ്ടിയുള്ള ടേബിൾ (Products Table)
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand_id TEXT,
    name TEXT NOT NULL,
    packing TEXT NOT NULL,
    mrp TEXT NOT NULL,
    img TEXT NOT NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
)
''')

# താൽക്കാലിക വിവരങ്ങൾ (Sample Data) ചേർക്കുന്നു
brands_data = [
    ('kopiko', 'Kopiko'),
    ('milma', 'Milma'),
    ('winkies', 'Winkies'),
    ('bouli', 'Bouli'),
    ('suraj_ada', 'Suraj Ada'),
    ('mother_dairy', 'Mother Dairy')
]

products_data = [
    ('kopiko', 'Kopiko Cappuccino Candy Pack', '140 g', '47.00', 'kopiko_candy.png'),
    ('kopiko', 'Kopiko Coffee Shot', '150 g', '150.00', 'kopiko_shot.png'),
    ('milma', 'Milma Toned Milk', '500 ml', '28.00', 'milma_milk.png'),
    ('milma', 'Milma Ghee', '200 ml', '152.00', 'milma_ghee.png'),
    ('milma', 'Milma Curd', '500 g', '35.00', 'milma_curd.png'),
    ('winkies', 'Winkies Mini Swiss Roll', '25 g', '10.00', 'winkies_roll.png'),
    ('bouli', 'Bouli Moonfils Croissant Choco', '45 g', '20.00', 'bouli_choco.png')
]

# ഡാറ്റാബേസിലേക്ക് മാറ്റുന്നു
cursor.executemany('INSERT OR IGNORE INTO brands VALUES (?, ?)', brands_data)
cursor.executemany('INSERT OR IGNORE INTO products (brand_id, name, packing, mrp, img) VALUES (?, ?, ?, ?, ?)', products_data)

conn.commit()
conn.close()
print("Database created and populated successfully!")