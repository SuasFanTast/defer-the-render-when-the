import threading
from flask import Flask, request, jsonify, abort, send_file
import sqlite3
import json
import os
import uuid
from datetime import datetime
import hashlib
import zipfile
from io import BytesIO

app = Flask(__name__)
DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)




#!!!!!!!!!!!!!
DB_con = None
#!!!!!!!!!!!!!

def get_db_connection():
    global DB_con
    if DB_con is None:
        DB_con = sqlite3.connect(DATABASE, timeout=10)
        DB_con.row_factory = sqlite3.Row
        return DB_con
    else:
        return DB_con

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data:
        return bad_request()

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute('SELECT ID FROM User WHERE username = ?', (username,))
    if cursor.fetchone():
        #conn.close()
        return jsonify({'error': 'User already exists'})

    # Insert new user
    cursor.execute('''
        INSERT INTO User (username, password, Node, Tokens)
        VALUES (?, ?, NULL, 0.0)
    ''', (username, password))
    conn.commit()
    #conn.close()

    return jsonify({'status': 'ok'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data:
        return bad_request()

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ID FROM User 
        WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    #conn.close()

    if not user:
        return jsonify({'error': 'Invalid credentials'})

    """
    session_key = str(uuid.uuid4())
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO Session (User, SessionKey, CreatedAt)
        VALUES (?, ?, ?)
    ''', (user['ID'], session_key, datetime.now()))
    conn.commit()
    conn.close()

    """
    return jsonify({
        'status': 'ok',
        'session_key': None
    })

@app.route('/stats', methods=['POST'])
def get_user_stats():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data:
        return bad_request()

    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ID FROM User 
        WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    #conn.close()

    if not user:
        return jsonify({'error': 'Invalid credentials'})

    user_id = user['ID']

    # Get all projects for this user
    conn = get_db_connection()
    cursor = conn.cursor()
    
    
    
    """cursor.execute('''
        SELECT * FROM Project 
        WHERE User = ?
    ''', (user_id,)) """



    cursor.execute('''
                   SELECT P.*, F.Size
                   FROM Project P
                   JOIN File F ON P.File = F.id
                   WHERE P.User = ?
                   ''', (user_id,))
    projects = [dict(row) for row in cursor.fetchall()]

    """
    # Get all files for this user
    cursor.execute('''
        SELECT * FROM File 
        WHERE User = ?
    ''', (user_id,))
    files = [dict(row) for row in cursor.fetchall()]
    """
    
    # Get all assets
    cursor.execute('''
        SELECT * FROM Asset 
        WHERE Project IN (SELECT ID FROM Project WHERE User = ?)
    ''', (user_id,))
    assets = [dict(row) for row in cursor.fetchall()]
    #print("==GETUSERSTATS== debug")
    #print(assets)
    # Get render results
    cursor.execute('''
        SELECT * FROM RenderResult 
        WHERE Project IN (SELECT ID FROM Project WHERE User = ?)
    ''', (user_id,))
    render_results = [dict(row) for row in cursor.fetchall()]


    cursor.execute("SELECT * FROM Node WHERE User=?",(user_id,))

    column_names = [desc[0] for desc in cursor.description]  # Get column names
    nodes_report = [dict(zip(column_names, row)) for row in cursor.fetchall()]  # Fetch data as dictionaries

    # Convert the fetched data to JSON
    nodes_report = json.dumps(nodes_report)
    #nodes_report = cursor.fetchmany()

    #nodes_report = json.dumps(nodes_report)

    #conn.close()
      #token_sum

      #!!deprecated AF!!
    """
    cursor.execute('''
            SELECT COALESCE(SUM(rr.tokens), 0)
            FROM RenderResult rr
            JOIN Node n ON rr."Node" = n.id
            WHERE n."User" = ?
        ''', (user_id,))
    
    tken= cursor.fetchone()
    tken=tken[0]
    """  
    #get all the funny files to be dealt on client-side
    cursor.execute("SELECT * FROM File WHERE User=?", (user_id,))

    column_names = [desc[0] for desc in cursor.description]  # Get column names
    files_report = [dict(zip(column_names, row)) for row in cursor.fetchall()]  # Fetch data as dictionaries



    return jsonify({
        'status': 'ok',
        'projects': projects,
        'files': files_report,
        'assets': assets,
        'render_results': render_results,
        'user_id':user_id,
        #'tokens':tken,
        'nodes':nodes_report
    })

def get_user_id(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ID FROM User 
        WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    #conn.close()
    return user['ID'] if user else None

@app.route('/add_asset', methods=['POST'])
def add_asset():
    print("ADD ASS ==debug==")
    print(request.form)
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    data = request.form
    if not data or not 'username' in data or not 'password' in data or not 'filename' in data:
        return jsonify({'error': 'Missing required fields'}), 400

    username = data['username']
    password = data['password']
    filename = data['filename']
    #project_name = data['project_name']
    
    #ass debug (конец глистам)
    print("====ASS PROJECT NAME")
    #print(project_name + " " + username + " " + filename)
    #print("====END OF ASS PROJECT NAME")


    user_id = get_user_id(username, password)
    if not user_id:
        print("адд асс плозие кредентиалься")
        return jsonify({'error': 'Invalid credentials'}), 401

    
    



    conn = get_db_connection()
    cursor = conn.cursor()

    #добавить запысь в БД
    
    """cursor.execute('''
        INSERT INTO File (Path, User, Name, Size, Date, Hash, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (file_path, user_id, filename, os.path.getsize(file_path), datetime.now(), hashlib.md5(uploaded_file.read()).hexdigest(), False))
    file_id = cursor.lastrowid
    """



    cursor.execute('''
        INSERT INTO File (Path, User, Name, Size, Date, Hash, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (0, user_id, filename, 0, datetime.now(), 0, False))
    file_id = cursor.lastrowid


    #стырить оттуда ID
    
    #записать в ФС с именем файла ID

    file_path = os.path.join(UPLOAD_FOLDER, str(file_id))
    uploaded_file.save(file_path)
    


    # вычистать хэшь
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    #update file entry
    cursor.execute('''
                   UPDATE File SET Path=?, Size=?, Hash=? WHERE ID=?
                   ''', (file_path, os.path.getsize(file_path), file_hash, file_id))

    """
    if 1:
        cursor.execute('''
            SELECT ID FROM Project 
            WHERE User = ? AND Name = ?
        ''', (user_id, project_name))
        project = cursor.fetchone()
        print("ASS")
        print(str(project) + " " + project_name + " userid " + str(user_id))
        print("/ASS")
        if project:
            cursor.execute('''
                INSERT INTO Asset (Project, File)
                VALUES (?, ?)
            ''', (project['ID'], file_id))
            conn.commit()
            
            print("add asset ok")
            return jsonify({'status': 'ok', 'file_id': file_id, 'asset_id': cursor.lastrowid})
        else:
            
            return jsonify({'error': 'Project not found'}), 404

    """

    conn.commit()
    #conn.close()
    return jsonify({'status': 'ok', 'file_id': file_id}), 201



@app.route('/bind_asset_to_project', methods=['POST'])
def bind_asset():
    #usual server routine
    print("BIND ASS ==DEBUG==")
    req = request.get_json()
    print(req)
    if not req or 'username' not in req or 'password' not in req or 'project' not in req or 'asset' not in req:
        print("BIND ASS BRUH!")
        return bad_request('Missing form data')
    
    username = req['username']
    password = req['password']
    project_name = req['project']
    asset_name = req['asset']
    action = req['action']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})
    
    #now it's database time

    cursor.execute('''
                   SELECT * FROM Project 
                   WHERE name=? AND user=? 
                                   
                   ''', (project_name, user_id))
    temp = cursor.fetchone()
    proj_id = temp['id']

    #==PROJECT_ID
    #select from Project where name==projName and userid== userid
    #temp = fetchone
    #proj_id = temp['id']


    cursor.execute('''
                   SELECT * FROM File
                   WHERE user=? AND name=?
                   ''',(user_id, asset_name))
    
    temp=cursor.fetchone()
    ass_id = temp['id']
    #==FILE_ID
    #select from File where userID == userID and name==assetname
    #temp2 = fetchone
    #ass_id = temp2['id']
    #insert into ass Project=proj_id, Asset=ass_id
    cursor.execute('''
                   INSERT INTO Asset
                   (Project, File)
                   VALUES (?,?)
                   ''', (proj_id,ass_id))

    conn.commit()
    return jsonify({'status': 'ok'})

    


@app.route('/delete_asset_byID', methods=['POST'])
def delete_asset_by_id():
    #usual server routine
    print("del ASS ==DEBUG==")
    req = request.get_json()
    print(req)
    if not req or 'username' not in req or 'password' not in req or 'assetID' not in req:
        print("DELETE ASS BRUH!")
        return bad_request('Missing form data')
    
    username = req['username']
    password = req['password']
    ass_id = req['assetID']
    
    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})
    
    cursor.execute('''
                   SELECT * FROM Project
                   WHERE User=?
                   ''', (user_id,))
    all_proj = cursor.fetchall()

    cursor.execute('''
                   SELECT * FROM Asset
                   WHERE ID=?
                   ''', (ass_id,))
    ass = cursor.fetchone()

    print(ass['project'])
    print(all_proj)
    for i in all_proj:
        if (i['ID'] == ass['project']):
            cursor.execute('''
                        DELETE FROM Asset
                        WHERE ID=?                    
                        ''', (ass_id,))
    print("end of delete ass by ID")

    return jsonify({'status': 'ok'})

@app.route('/add_project', methods=['POST'])
def add_project():
    if 'file' not in request.files:
        return bad_request('No file part')

    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return bad_request('No selected file')

    if not request.form or not 'username' in request.form or not 'password' in request.form or not 'project_name' in request.form:
        return bad_request('Missing form data')

    username = request.form['username']
    password = request.form['password']
    project_name = request.form['project_name']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})


    conn = get_db_connection()
    cursor = conn.cursor()


    # добавтиь файл в БД
    """cursor.execute('''
        INSERT INTO File (Path, User, Size, Date, Hash, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (file_path, user_id, os.path.getsize(file_path), datetime.now(), file_hash, False))
    file_id = cursor.lastrowid
    """

    cursor.execute('''
        INSERT INTO File (Path, User, Size, Date, Hash, IsDeleted, Name)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (0, user_id, 0, datetime.now(), 0, False, project_name))
    file_id = cursor.lastrowid
    #сохранить файл в ФС
    file_path = os.path.join(UPLOAD_FOLDER, str(file_id))
    uploaded_file.save(file_path)

    # вычистать хэшь
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    #update file entry
    cursor.execute('''
                   UPDATE File SET Path=?, Size=?, Hash=? WHERE ID=?
                   ''', (file_path, os.path.getsize(file_path), file_hash, file_id))

    print("PROJ TABLE::::::" + str(user_id) + " " + str(file_id) + "  " + str(project_name))
    cursor.execute('''
        INSERT INTO Project (User, RenderResult, File, Name, Program, RAMrequirementMB, VRAMrequirementMB, Priority)
        VALUES (?, NULL, ?, ?, 1, 0, 0, 0)
    ''', (user_id, file_id, str(project_name)))
    project_id = cursor.lastrowid

    conn.commit()
    #conn.close()

    return jsonify({'status': 'ok', 'project_id': project_id, 'file_id': file_id})

@app.route('/run', methods=['POST'])
def run_project():
    return jsonify({
        "function_response":"OK",
        "easter egg":"found"
    })
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data or not 'project_name' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    project_name = data['project_name']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ID FROM Project 
        WHERE User = ? AND Name = ?
    ''', (user_id, project_name))
    project = cursor.fetchone()
    conn.close()

    if not project:
        return jsonify({'error': 'Project not found'})

    # Add project ID to task queue (placeholder functionality)
    return jsonify({'status': 'ok', 'task_id': str(uuid.uuid4())})

@app.route('/delete_asset', methods=['POST'])
def delete_asset():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data or not 'asset_name' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    asset_name = data['asset_name']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    # Find asset and its file
    cursor.execute('''
        SELECT Asset.ID AS asset_id, File.ID AS file_id, File.Path AS file_path
        FROM Asset 
        JOIN File ON Asset.File = File.ID
        WHERE File.Name = ? AND File.User = ?
    ''', (asset_name, user_id))
    asset = cursor.fetchone()

    if not asset:
        #conn.close()
        return jsonify({'error': 'Asset not found'})

    # Delete file from filesystem
    if os.path.exists(asset['file_path']):
        os.remove(asset['file_path'])

    # Delete from database
    cursor.execute('''
        DELETE FROM Asset WHERE ID = ?
    ''', (asset['asset_id'],))

    cursor.execute('''
        DELETE FROM File WHERE ID = ?
    ''', (asset['file_id'],))

    conn.commit()
    #conn.close()

    return jsonify({'status': 'ok'})



@app.route('/delete_project', methods=['POST'])
def delete_project():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data or not 'project_name' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    project_name = data['project_name']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    """
    cursor.execute('''
        SELECT Project.ID, Project.File, RenderResult.File 
        FROM Project 
        WHERE Project.User = ? AND Project.Name = ?
    ''', (user_id, project_name))
    result = cursor.fetchone()
        #LEFT JOIN RenderResult ON Project.ID = RenderResult.Project 

        """

    cursor.execute('''
        SELECT Project.ID, Project.File
        FROM Project 
        WHERE Project.User = ? AND Project.Name = ?
    ''', (user_id, project_name))
    result = cursor.fetchone();

    print("DELPROJ=== " + str(result))

    if not result:
        #conn.close()
        return jsonify({'error': 'Project not found'})

    """
    # Delete files from filesystem
    def delete_file(file_id):
        
        cursor.execute('''
            SELECT Path FROM File WHERE ID = ?
        ''', (file_id,))
        file = cursor.fetchone()
        if file and os.path.exists(file['Path']):
            os.remove(file['Path'])
    """

    #delete_file(result['File'])
    #if result['RenderResult']:
        #delete_file(result['RenderResult'])

    # Delete from database
    print("====DEBUG_ DEL PROJ===")
    print(str(result['ID']) + " bruh")
    
    cursor.execute('''
                   DELETE FROM Project WHERE ID=?
                   ''', (result['ID'], ))
    conn.commit()

        #Custom logick do delete all render results::
        #select from redner result where project  = id; fetch many, iterate oer tht shit to delete all files
    """cursor.execute('''
        DELETE FROM Project WHERE ID = ?
    ''', (result['Project'],))

    cursor.execute('''
        DELETE FROM RenderResult WHERE Project = ?
    ''', (result['Project'],))

    conn.commit()
    #conn.close()
    """
    return jsonify({'status': 'ok'})




@app.route('/start_project', methods=['POST'])
def start_project():
    #usual server routine
    print("satrt ==DEBUG==")
    req = request.get_json()
    print(req)
    if not req or 'username' not in req or 'password' not in req or 'projId' not in req :
        
        return bad_request('Missing form data')
    
    username = req['username']
    password = req['password']
    pid = req['projId']
    
    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})
    
    #database time

    #check to see if this project is users'
    cursor.execute('''
                   UPDATE Project
                   SET Priority=400
                   WHERE user=? AND ID=?
                   ''', (user_id,pid))
    conn.commit()
    
    #server response
    return jsonify({'status': 'ok'})



@app.route('/download_render_result', methods=['POST'])
def download_render_result():
    data = request.get_json()
    proj_id = request.args.get('proj_id')
    if not data or not 'username' in data or not 'password' in data or not 'proj_id' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    proj_id = data['proj_id']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    """
    cursor.execute('''
        SELECT Project.ID FROM Project 
        WHERE User = ? AND Name = ?
    ''', (user_id, project_name))
    project = cursor.fetchone()
    if not project:
        #conn.close()
        return jsonify({'error': 'Project not found'})

    """
    
    cursor.execute('''
        SELECT File.Hash, File.Name FROM RenderResult 
        JOIN File ON RenderResult.File = File.ID
        WHERE Project = ?
    ''', (proj_id,))
    files = [dict(row) for row in cursor.fetchall()]
    print(files)
    #files = cursor.fetchall()
    #conn.close()

   


    #conn.close()

    # Placeholder for file transfer logic
    return jsonify({'status': 'ok', 'files': files})

@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    node_id = data['node_id']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE Node SET User=? WHERE ID=?", (user_id,node_id))

    conn.commit()
    #conn.close()

    return jsonify({'status': 'ok'})

@app.route('/unlink_node', methods=['POST'])
def unlink_node():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data or not 'node_id' in data:
        return bad_request()

    username = data['username']
    password = data['password']
    node_id = data['node_id']

    user_id = get_user_id(username, password)
    if not user_id:
        return jsonify({'error': 'Invalid credentials'})

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM Node 
        WHERE ID = ? AND User = ?
    ''', (node_id, user_id))
    conn.commit()
    #conn.close()

    return jsonify({'status': 'ok'})

def get_user_id(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT ID FROM User 
        WHERE username = ? AND password = ?
    ''', (username, password))
    user = cursor.fetchone()
    #conn.close()
    return user['ID'] if user else None

def validate_credentials(username, password):
    return get_user_id(username, password) is not None

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("bruh")

    app.run(host='127.0.0.1', port=5000)
    
