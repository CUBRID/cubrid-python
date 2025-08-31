# -*- encoding:utf-8 -*-

import unittest
import CUBRIDdb
import time
import sys
import decimal
import datetime
from xml.dom import minidom

class CUBRIDdb_crud_test(unittest.TestCase):
    driver = CUBRIDdb
    
    xmlt = minidom.parse('python_config.xml')
    ips = xmlt.childNodes[0].getElementsByTagName('ip')
    ip = ips[0].childNodes[0].toxml()
    ports = xmlt.childNodes[0].getElementsByTagName('port')
    port = ports[0].childNodes[0].toxml()
    dbnames = xmlt.childNodes[0].getElementsByTagName('dbname')
    dbname = dbnames[0].childNodes[0].toxml()
    conStr = "CUBRID:"+ip+":"+port+":"+dbname+":::"
    
    connect_args = (conStr, 'dba', '')
    connect_kw_args = {}
    connect_kw_args2 = {'charset': 'utf8'}

    table_name = 'test_crud_table'

    def setUp(self):
        self.con = self.driver.connect(*self.connect_args, **self.connect_kw_args)
        self.cur = self.con.cursor()
        
    def tearDown(self):
        if hasattr(self, 'cur'):
            self.cur.close()
        if hasattr(self, 'con'):
            self.con.close()

    def test_01_create_table(self):
        print("\n=== Test : Create Table ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        self.con.commit()
        
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        
        self.cur.execute(create_sql.format(self.table_name))
        self.con.commit()
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        result = self.cur.fetchone()
        self.assertEqual(result[0], 0, "Newly created table should be empty")
        
        print("✓ Table creation successful")

    def test_02_insert_data(self):
        print("\n=== Test : Insert Data ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        self.con.commit()
        
        insert_sql = """
        INSERT INTO {0}
        (name, age, birth_date, created_at, height, weight, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        test_data = [
            ('홍길동', 30, '1993-05-15', '2023-01-01 10:00:00', 175.5, 70.2, '첫 번째 user'),
            ('Kim Cheolsu', 25, '1998-08-20', '2023-01-02 11:30:00', 180.0, 75.8, '두 번째 user'),
            ('이영희', 28, '1995-12-10', '2023-01-03 09:15:00', 165.3, 55.1, '세 번째 user'),
            ('박민수', 35, '1988-03-25', '2023-01-04 14:45:00', 178.2, 82.5, '네 번째 user'),
            ('최지영', 22, '2001-07-08', '2023-01-05 16:20:00', 162.8, 48.9, '다섯 번째 user')
        ]
        
        for data in test_data:
            self.cur.execute(insert_sql.format(self.table_name), data)
        
        self.con.commit()
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        result = self.cur.fetchone()
        self.assertEqual(result[0], 5, "5 rows of data should be inserted")
        
        print("✓ Data insertion successful")

    def test_03_select_data(self):
        print("\n=== Test : Select Data ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        
        insert_sql = """
        INSERT INTO {0}
        (name, age, birth_date, created_at, height, weight, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        test_data = [
            ('홍길동', 30, '1993-05-15', '2023-01-01 10:00:00', 175.5, 70.2, '첫 번째 user'),
            ('Kim Cheolsu', 25, '1998-08-20', '2023-01-02 11:30:00', 180.0, 75.8, '두 번째 user'),
            ('이영희', 28, '1995-12-10', '2023-01-03 09:15:00', 165.3, 55.1, '세 번째 user')
        ]
        
        for data in test_data:
            self.cur.execute(insert_sql.format(self.table_name), data)
        
        self.con.commit()
        
        self.cur.execute("SELECT * FROM {0} ORDER BY id".format(self.table_name))
        all_rows = self.cur.fetchall()
        self.assertEqual(len(all_rows), 3, "3 rows of data should be selected")
        
        self.cur.execute("SELECT name, age FROM {0} WHERE age > 25 ORDER BY age".format(self.table_name))
        filtered_rows = self.cur.fetchall()
        self.assertEqual(len(filtered_rows), 2, "age over 25 user should be 2")
        
        self.cur.execute("SELECT AVG(age), MAX(height), MIN(weight) FROM {0}".format(self.table_name))
        agg_result = self.cur.fetchone()
        self.assertIsNotNone(agg_result, "Aggregate result should be present")
        
        print("✓ Data selection successful")
        print("  - Total data: {0}".format(len(all_rows)))
        print("  - Age over 25: {0}".format(len(filtered_rows)))
        print("  - Average age: {0:.1f}".format(agg_result[0]))

    def test_04_update_data(self):
        print("\n=== Test : Update Data ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        
        insert_sql = """
        INSERT INTO {0}
        (name, age, birth_date, created_at, height, weight, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        test_data = [
            ('홍길동', 30, '1993-05-15', '2023-01-01 10:00:00', 175.5, 70.2, '첫 번째 user'),
            ('Kim Cheolsu', 25, '1998-08-20', '2023-01-02 11:30:00', 180.0, 75.8, '두 번째 user')
        ]
        
        for data in test_data:
            self.cur.execute(insert_sql.format(self.table_name), data)
        
        self.con.commit()
        
        self.cur.execute("SELECT name, age, height FROM {0} WHERE name = '홍길동'".format(self.table_name))
        before_update = self.cur.fetchone()
        self.assertEqual(before_update[1], 30, "Before update age should be 30")
        
        update_sql = """
        UPDATE {0}
        SET age = ?, height = ?, description = ? 
        WHERE name = ?
        """
        self.cur.execute(update_sql.format(self.table_name), (31, 176.0, '수정된 user 정보', '홍길동'))
        self.con.commit()
        
        self.cur.execute("SELECT name, age, height, description FROM {0} WHERE name = '홍길동'".format(self.table_name))
        after_update = self.cur.fetchone()
        self.assertEqual(after_update[1], 31, "After update age should be 31")
        self.assertEqual(after_update[2], 176.0, "After update height should be 176.0")
        self.assertEqual(after_update[3], u'수정된 user 정보', "After update description should be changed")
        
        print("✓ Data update successful")
        print("  - 홍길동's age: {0} → {1}".format(before_update[1], after_update[1]))
        print("  - 홍길동's height: {0} → {1}".format(before_update[2], after_update[2]))

    def test_05_delete_data(self):
        print("\n=== Test : Delete Data ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        
        insert_sql = """
        INSERT INTO {0}
        (name, age, birth_date, created_at, height, weight, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        test_data = [
            ('홍길동', 30, '1993-05-15', '2023-01-01 10:00:00', 175.5, 70.2, '첫 번째 user'),
            ('Kim Cheolsu', 25, '1998-08-20', '2023-01-02 11:30:00', 180.0, 75.8, '두 번째 user'),
            ('이영희', 28, '1995-12-10', '2023-01-03 09:15:00', 165.3, 55.1, '세 번째 user')
        ]
        
        for data in test_data:
            self.cur.execute(insert_sql.format(self.table_name), data)
        
        self.con.commit()
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        before_delete = self.cur.fetchone()[0]
        self.assertEqual(before_delete, 3, "Before delete 3 rows of data should be present")
        
        delete_sql = "DELETE FROM {0} WHERE age < 27".format(self.table_name)
        self.cur.execute(delete_sql)
        self.con.commit()

        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        after_delete = self.cur.fetchone()[0]
        self.assertEqual(after_delete, 2, "After delete 2 rows of data should be present")
        
        self.cur.execute("SELECT name FROM {0} WHERE age < 27".format(self.table_name))
        deleted_data = self.cur.fetchall()
        self.assertEqual(len(deleted_data), 0, "All data under 27 years old should be deleted")
        
        print("✓ Data deletion successful")
        print("  - Before delete: {0} rows".format(before_delete))
        print("  - After delete: {0} rows".format(after_delete))

    def test_06_drop_table(self):
        print("\n=== Test : Drop Table ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        result = self.cur.fetchone()
        self.assertEqual(result[0], 0, "Table should be created")
        
        drop_sql = "DROP TABLE {0}".format(self.table_name)
        self.cur.execute(drop_sql)
        self.con.commit()
        
        try:
            self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
            self.fail("Table should be deleted")
        except Exception as e:
            print("✓ Table deletion successful")
            print("  - Error message: {0}".format(str(e)))

    def test_07_complex_crud_operations(self):
        print("\n=== Test : Complex CRUD Operations ===")
        
        self.cur.execute('DROP TABLE IF EXISTS {0}'.format(self.table_name))
        create_sql = """
        CREATE TABLE {0} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            age INT,
            birth_date DATE,
            created_at DATETIME,
            height FLOAT,
            weight DOUBLE,
            description VARCHAR(500)
        )
        """
        self.cur.execute(create_sql.format(self.table_name))
        
        insert_sql = """
        INSERT INTO {0}
        (name, age, birth_date, created_at, height, weight, description) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        test_data = [
            ('김철수', 25, '1998-08-20', '2023-01-02 11:30:00', 180.0, 75.8, '첫 번째 사용자'),
            ('이영희', 28, '1995-12-10', '2023-01-03 09:15:00', 165.3, 55.1, '두 번째 사용자'),
            ('박민수', 35, '1988-03-25', '2023-01-04 14:45:00', 178.2, 82.5, '세 번째 사용자')
        ]
        
        for data in test_data:
            self.cur.execute(insert_sql.format(self.table_name), data)
        
        self.con.commit()
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        count = self.cur.fetchone()[0]
        self.assertEqual(count, 3, "3 rows of data should be inserted")
        
        update_sql = "UPDATE {0} SET age = age + 1 WHERE age < 30".format(self.table_name)
        self.cur.execute(update_sql)
        self.con.commit()
        
        self.cur.execute("SELECT name, age FROM {0} WHERE name IN ('김철수', '이영희') ORDER BY name".format(self.table_name))
        updated_rows = self.cur.fetchall()
        self.assertEqual(updated_rows[0][1], 26, "김철수's age should be 26")
        self.assertEqual(updated_rows[1][1], 29, "이영희's age should be 29")
        
        delete_sql = "DELETE FROM {0} WHERE age > 30".format(self.table_name)
        self.cur.execute(delete_sql)
        self.con.commit()
        
        self.cur.execute("SELECT COUNT(*) FROM {0}".format(self.table_name))
        final_count = self.cur.fetchone()[0]
        self.assertEqual(final_count, 2, "After delete 2 rows of data should be present")
        
        self.cur.execute("DROP TABLE {0}".format(self.table_name))
        self.con.commit()

        print("✓ Complex CRUD operations successful")
        print("  - Initial data: 3 rows")
        print("  - Age increase under 30: 2 rows")
        print("  - After delete over 30: {0} rows".format(final_count))

def suite():
    suite = unittest.TestSuite()
    suite.addTest(CUBRIDdb_crud_test("test_01_create_table"))
    suite.addTest(CUBRIDdb_crud_test("test_02_insert_data"))
    suite.addTest(CUBRIDdb_crud_test("test_03_select_data"))
    suite.addTest(CUBRIDdb_crud_test("test_04_update_data"))
    suite.addTest(CUBRIDdb_crud_test("test_05_delete_data"))
    suite.addTest(CUBRIDdb_crud_test("test_06_drop_table"))
    suite.addTest(CUBRIDdb_crud_test("test_07_complex_crud_operations"))
    return suite

if __name__ == '__main__':
    log_file = 'test_CUBRIDdb_crud.result'
    f = open(log_file, "w")
    suite = unittest.TestLoader().loadTestsFromTestCase(CUBRIDdb_crud_test)
    unittest.TextTestRunner(verbosity=2, stream=f).run(suite)
    f.close()
