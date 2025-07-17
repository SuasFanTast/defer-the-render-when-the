import threading
from flask import Flask, request, jsonify, abort, send_file
import sqlite3
import time
import json
import os
import uuid
from datetime import datetime
import hashlib
from time import sleep
import subprocess



app = Flask(__name__)

const_proj_ready = 400;
const_proj_running = 399;
const_nodestate_ready = 1;
const_nodestate_sent = 2;
const_nodestate_unbound  = -1;

const_RRstate_queued = 10;
const_RRstate_sent = 11;
const_RRstate_finished = 20;

DATABASE = 'database.db'
UPLOAD_FOLDER = 'uploads_2'
BLENDER_PATH = '/home/sergei/New Folder/bilshut_Locale/~~Spring2025/DB/ExperimentV3/Node/blender-4.4.3-linux-x64/blender-launcher'
HELPER_SCRIPT_PATH = '/home/sergei/New Folder/bilshut_Locale/~~Spring2025/DB/ExperimentV3/_HELPER_fetchFrame.py'

DB_con = None


#dipshit algo
#proj_queue = []
#node_pool = []
#node_task = []
#node_task_files = [] #init this with every node ID 


def get_db_connection():
    global DB_con
    if DB_con is None:
        DB_con = sqlite3.connect(DATABASE, timeout=10)
        DB_con.row_factory = sqlite3.Row
        return DB_con
    else:
        return DB_con


def init():
    
    DB_conL = sqlite3.connect(DATABASE, timeout=10)
    DB_conL.row_factory = sqlite3.Row
    cur = DB_conL.cursor()

    """
    last_id = cur.execute("SELECT ID FROM Node ORDER BY ID DESC LIMIT 1").fetchone()

    for i in range(last_id['ID']):
        node_task_files.append([i])
        node_pool.append(0)
    


    proj_queue = 0
    """    


def algo():
    #algorhitm placeholder
    error = 0
    
    while (not error):
        sleep(5)
        DB_conL = sqlite3.connect(DATABASE, timeout=10)
        DB_conL.row_factory = sqlite3.Row
        c = DB_conL.cursor()

        #print("i'm alive!!")
        #poll DB for projects
        #poll DB for nodes
        #for each project add them to nodes, that have "wait" online state (200)

        c.execute("SELECT * FROM Project WHERE Priority = ?  ", (const_proj_ready,))
        proj_arr = c.fetchall()
        try:
            pass
            #print(proj_arr[0]['id']) # array of ROW of project
        except:
            pass
        #unbusy online nodes
        c.execute("SELECT * FROM Node WHERE state=? AND lastPing >= DATETIME('now','-1 minute')" , (const_nodestate_ready,))
        node_pool = c.fetchall()
        #print(node_pool)# array of ROW of Nodes that satisfy "SOME" conditions

        #add le render result table, into INFO store JSON: workseptype:byframe1, framestart:int, frameend:int,
        proj_index = -1
        for node in node_pool:
            RRinfo = json.dumps({"workseptype":"NodeProjRobinRound"})
            #execute cursor and add RR 
            proj_index += 1
            #try:
            if proj_index < len(proj_arr):
                c.execute("INSERT INTO RenderResult (Project,Node,Info) VALUES (?,?,?)",
                      (proj_arr[proj_index]['id'],node['ID'],RRinfo))
                c.execute("UPDATE Project SET Priority=? WHERE ID=?", (const_proj_running, proj_arr[proj_index]['id']))
            else:
                print("more nodes than projects bruh")
                break
       
        DB_conL.commit()
        DB_conL.close()
        

        
def algo_v2_frameSplit():
    error = 0
    while not error:
        sleep(5)
        DB_conL = sqlite3.connect(DATABASE, timeout=10)
        DB_conL.row_factory = sqlite3.Row
        c = DB_conL.cursor()

        # Fetch projects that are ready for rendering
        c.execute("SELECT * FROM Project WHERE Priority = ?", (const_proj_ready,))
        proj_arr = c.fetchall()

        # Fetch online nodes in "ready" state (within the last minute)
        c.execute("SELECT * FROM Node WHERE state=? AND lastPing >= DATETIME('now','-1 minute')", (const_nodestate_ready,))
        node_pool = c.fetchall()

        # Only proceed if we have both projects and nodes
        if node_pool and proj_arr:
            for project in proj_arr:
                # Step 1: Get the .blend file path for the project
                c.execute("""
                    SELECT Path FROM File
                    WHERE ID = (SELECT File FROM Project WHERE ID = ?)
                """, (project['id'],))
                fpath_row = c.fetchone()
                if not fpath_row:
                    continue  # Skip if no file path found

                blend_path = fpath_row['Path']

                # Step 2: Use Blender to extract frame range
                try:
                    result = subprocess.run(
                        [BLENDER_PATH, '-b', blend_path, '-P', HELPER_SCRIPT_PATH],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True,
                        text=True,
                        timeout=10
                    )

                    frame_start = None
                    frame_end = None
                    for line in result.stdout.splitlines():
                        if line.startswith('start:'):
                            frame_start = int(line.split(':')[1].strip())
                        elif line.startswith('end:'):
                            frame_end = int(line.split(':')[1].strip())

                    if frame_start is None or frame_end is None:
                        continue  # Invalid frame data

                except Exception as e:
                    print(f"Error processing project {project['id']}: {e}")
                    continue

            # Step 3: Distribute each frame as a separate RenderResult
            num_nodes = len(node_pool)
            frames = list(range(frame_start, frame_end + 1))

            for frame_index, frame in enumerate(frames):
                node = node_pool[frame_index % num_nodes]  # Round-robin assignment

                info = {
                    "workseptype": "singleFrameSplit|1",
                    "framestart": frame,
                    "frameend": frame
                }

                info_json = json.dumps(info)

                # Step 4: Insert RenderResult for this frame
                c.execute("""
                    INSERT INTO RenderResult (Project, Node, Info)
                    VALUES (?, ?, ?)
                """, (project['id'], node['ID'], info_json))

            # Step 5: Mark the project as running
            c.execute("UPDATE Project SET Priority = ? WHERE ID = ?", 
                     (const_proj_running, project['id']))

        DB_conL.commit()
        DB_conL.close()
















        

"""

@app.route("/api2", methods=['POST'])
def api2call():
    #1)boilerplate setup
    bruh = request.form
    #print(bruh)
    #====
    
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tsk = None
    form_filetable = None    


    #2) fun part of processing whatever got sent here
    program = None


    if 'id' in bruh:
        
        if int(bruh['id']) == -1:
            
            cursor.execute("INSERT INTO Node (State) VALUES (?)", (-1,))
            id = cursor.lastrowid

            print("LASTROWID ===   " + str(id) + str(bruh['id']))
        else:
            id = bruh['id']
            print("SAMEID===" + str(id))

    else:
        return jsonify({"status":"Bad request / 22"})

    
    
    #make online
    if 'ping' in bruh:
        cursor.execute("UPDATE Node SET state=?, lastPing=DATETIME('NOW') WHERE ID=?", (const_nodestate_ready, id))
        pass



    """









@app.route("/api2", methods=['POST'])
def api2call():


    bruh = request.form
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    benchmark_trigger = False

    tsk = None
    form_filetable = None
    proj_name_sent = None
    method_sep = None

    if 'id' in bruh:
        if int(bruh['id']) == const_nodestate_unbound:
            cursor.execute("INSERT INTO Node (State) VALUES (?)", (const_nodestate_ready,))
            id = cursor.lastrowid
            #add benchmarking RR here
            benchmark_trigger = True
            cursor.execute("INSERT INTO RenderResult (Project,Node,Info) VALUES (?,?,?)",
                      (-1,id,"benchmark"))

        else:
            id = int(bruh['id'])  # Convert to integer
    else:
        return jsonify({"status": "Bad request / 22"})

    if 'ping' in bruh:
        cursor.execute("UPDATE Node SET state=?, lastPing=DATETIME('NOW') WHERE ID=?", (const_nodestate_ready, id))


    """ #old code that did something
    #software support report
    if 'program' in bruh:
        program = bruh['program']

    if 'plugin' in bruh:
        plugin_name = bruh['plugin']
        plugin_version = bruh['plugin_ver']

    
    #harware support report
    if 'cpu' in bruh:
        cpu_name = bruh['cpu']
        speed = bruh['cpu_speed']
        cores = bruh['cpu_cores']

    if 'gpu' in bruh:
        gpu_name = bruh['gpu']
        vram = bruh['vram'] 
    
    if 'ram' in bruh:
        #TODO:: redo database, add ram column to Node table
        pass
    """
    # Collect software data from 
    program = bruh.get('program')
    program_ver = bruh.get('program_ver')
    plugin = bruh.get('plugin')
    plugin_ver = bruh.get('plugin_ver')

    # Collect hardware data from 
    cpu_name = bruh.get('cpu')
    cpu_speed = bruh.get('cpu_speed')
    cpu_cores = bruh.get('cpu_cores')
    gpu_name = bruh.get('gpu')
    vram = bruh.get('vram')
    ram = bruh.get('ram')
    free_space = bruh.get('free_space')
    files = bruh.get('files')


    ###HARDWARE UPDATE CODE###
    ##PLEASE TEST THIS STUPID SHIT
    # Handle CPU insertion or retrieval
    cpu_id = None
    if cpu_name and cpu_speed and cpu_cores:
        cursor.execute(
            "SELECT id FROM CPU WHERE name=? AND speed=? AND cores=?", 
            (cpu_name, cpu_speed, cpu_cores)
        )
        row = cursor.fetchone()
        if row:
            cpu_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO CPU (name, speed, cores) VALUES (?, ?, ?)", 
                (cpu_name, cpu_speed, cpu_cores)
            )
            cpu_id = cursor.lastrowid

    # Handle GPU insertion or retrieval
    gpu_id = None
    if gpu_name and vram:
        cursor.execute(
            "SELECT id FROM GPU WHERE name=? AND vram=?", 
            (gpu_name, vram)
        )
        row = cursor.fetchone()
        if row:
            gpu_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO GPU (name, vram) VALUES (?, ?)", 
                (gpu_name, vram)
            )
            gpu_id = cursor.lastrowid

    # Handle HWconfig insertion or retrieval using CPU and GPU IDs
    hwconfig_id = None
    if cpu_id and gpu_id:
        cursor.execute(
            "SELECT id FROM HWconfig WHERE CPU=? AND GPU=?", 
            (cpu_id, gpu_id)
        )
        row = cursor.fetchone()
        if row:
            hwconfig_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO HWconfig (CPU, GPU) VALUES (?, ?)", 
                (cpu_id, gpu_id)
            )
            hwconfig_id = cursor.lastrowid

    # Handle Program insertion or retrieval
    program_id = None
    if program:
        cursor.execute("SELECT ID FROM Program WHERE Name=?", (program,))
        row = cursor.fetchone()
        if row:
            program_id = row[0]
        else:
            cursor.execute("INSERT INTO Program (Name) VALUES (?)", (program,))
            program_id = cursor.lastrowid

    # Handle Plugin insertion or retrieval
    plugin_id = None
    if plugin and plugin_ver:
        cursor.execute("SELECT ID FROM Plugin WHERE Name=? AND Version=?", (plugin, plugin_ver))
        row = cursor.fetchone()
        if row:
            plugin_id = row[0]
        else:
            cursor.execute("INSERT INTO Plugin (Name, Version) VALUES (?, ?)", (plugin, plugin_ver))
            plugin_id = cursor.lastrowid

    # Handle ProgramPlugin insertion or retrieval
    program_plugin_id = None
    if program_id and plugin_id:
        cursor.execute(
            "SELECT * FROM ProgramPlugin WHERE Program=? AND Plugin=?", 
            (program_id, plugin_id)
        )
        row = cursor.fetchone()
        if row:
            program_plugin_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO ProgramPlugin (Program, Plugin) VALUES (?, ?)", 
                (program_id, plugin_id)
            )
            program_plugin_id = cursor.lastrowid

    # Handle SWConfig insertion or retrieval
    swconfig_id = None
    if id and program_plugin_id:
        cursor.execute(
            "SELECT * FROM SWConfig WHERE Node=? AND ProgramPlugin=?", 
            (id, program_plugin_id)
        )
        row = cursor.fetchone()
        if row:
            swconfig_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO SWConfig (Node, ProgramPlugin) VALUES (?, ?)", 
                (id, program_plugin_id)
            )
            swconfig_id = cursor.lastrowid

    # Update Node table with hardware and software configuration IDs
    try:
        """files was removed because f#ck you"""
        cursor.execute("""
            INSERT INTO Node (
                ID, HWConfig, SWConfig, ram, FreeSpaceMB
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (ID) DO UPDATE SET
                HWConfig = COALESCE(excluded.HWConfig, HWConfig),
                SWConfig = COALESCE(excluded.SWConfig, SWConfig),
                ram = COALESCE(excluded.ram, ram),
                FreeSpaceMB = COALESCE(excluded.FreeSpaceMB, FreeSpaceMB)
        """, (
            id, hwconfig_id, swconfig_id, ram, free_space
        ))
    except sqlite3.Error as e:
        print("Database exception:", e)
        
###HARDWARE UPDATE CODE END###
    """
    if 'freespace' in bruh:
        free_space = bruh['free_space']
"""
    file_list = []
    #input files report
    """
    if 'files' in bruh:
        something = json.loads(bruh['files'])
        if something is not None:
            for file in something:
                
                fhash = file['hash']
                fname = file['name']
                fsize = file['size']
                file_list.append([fhash,fname,fsize])  #nodefile table 
    """
                

    """
    #output files report
    if 'result' in bruh:
        renderresfile = request.files['result']
        renderresfilename = bruh['result_filename']
        proj_id = bruh['proj_id']
        render_time = bruh['render_time']
        #put the file in the database and add result to the FS with logick from server1
    """
    if 'error' in bruh:
        error = bruh['error']
        #logick to process errore

    ###new code that updates nodefiles, please test this, this definetly not buggy 
    # Process files from node metadata
    if 'files' in bruh:
        #print(bruh['files'])
        node_files = json.loads(bruh['files'])  # List of file metadata
        current_file_hashes = set()  # To track which files are present in current metadata

        # Process each file from the node's metadata
        for file_meta in node_files:
            fname = file_meta.get('name')
            fhash = file_meta.get('hash')
            if not fname or not fhash:
                continue  # Skip invalid entries

            # Find matching File in database by name and hash
            cursor.execute("SELECT ID FROM File WHERE Name=? AND Hash=?", (fname, fhash))
            file_row = cursor.fetchone()
            if file_row:
                file_id = file_row['ID']
                current_file_hashes.add(file_id)

                # Check if this NodeFile entry exists
                cursor.execute("SELECT 1 FROM NodeFile WHERE Node=? AND File=?", (id, file_id))
                if not cursor.fetchone():
                    # Insert new NodeFile entry
                    cursor.execute("INSERT INTO NodeFile (Node, File) VALUES (?, ?)", (id, file_id))


        """
        # Now, delete NodeFile entries for this Node that are not in current_file_hashes
        # Get all existing NodeFile entries for this Node
        cursor.execute("SELECT File FROM NodeFile WHERE Node=?", (id,))
        existing_files = cursor.fetchall()
        for row in existing_files:
            file_id = row['File']
            if file_id not in current_file_hashes:
                # Delete this entry
                cursor.execute("DELETE FROM NodeFile WHERE Node=? AND File=?", (id, file_id))
        """




    


    #logick for updating the RR in case when task is actually complete
    if 'finished' in bruh:
        if bruh['finished'] == 'ok':
            RRid = bruh['RRid']
            
            cursor.execute("SELECT Project FROM RenderResult WHERE ID=?", (RRid,)) 
            pr_id = cursor.fetchone()[0]
            if pr_id < 0:
                #benchmark logick
                pass
                render_result_file = request.files['result']
                
                
                cursor.execute('''
                        INSERT INTO File (Path, Size, Date, Hash, IsDeleted, Name)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (0, 0, datetime.now(), 0, False, str(bruh['result_filename'])))
                file_id = cursor.lastrowid
                cursor.execute("UPDATE RenderResult SET End = DATETIME('now'),File=? WHERE id=?", (file_id,RRid))

                cursor.execute('INSERT INTO NodeBenchmark (Node,Benchmark,RenderResult) VALUES (?,?,?)'
                               ,(id,0,RRid))

                

                #add custom caveman brain logick because complex shit just sucks ass
                cursor.execute("SELECT * FROM RenderResult WHERE ID=?", (RRid,))
                RRrow = cursor.fetchone()
                st = RRrow['Start']
                nd = RRrow['End']

                st =int( time.mktime(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timetuple()))
                nd =int( time.mktime(datetime.strptime(nd, "%Y-%m-%d %H:%M:%S").timetuple()))
                
                bench_formula = int((1 / (nd - st + 1))*1000)
                print(bench_formula, " BENCCHMARKED NODE: ", id, "")
                #print("====TIME IS ====" + str(st - nd))

                cursor.execute("INSERT INTO NodeBenchmark (Benchmark, Node, RenderResult) VALUES (?,?,?)", (bench_formula,id,RRid))
                """
                
                cursor.execute('''
                    UPDATE NodeBenchmark
                    SET Benchmark = (
                        SELECT (JULIANDAY(r.End) - JULIANDAY(r.Start)) * 86400 * ?
                        FROM RenderResult r
                        WHERE r.ID = NodeBenchmark.RenderResult
                        AND r.Node = ?
                    )
                    WHERE EXISTS (
                        SELECT 1
                        FROM RenderResult r
                        WHERE r.ID = NodeBenchmark.RenderResult
                        AND r.Node = ?
                    )
                ''', (1, id, id))

"""
            else:
                render_result_file = request.files['result']
                
                cursor.execute('''
                        INSERT INTO File (Path, Size, Date, Hash, IsDeleted, Name)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (0, 0, datetime.now(), 0, False, str(bruh['result_filename'])))
                file_id = cursor.lastrowid
                




                file_name = bruh['result_filename']
                file_path = os.path.join(UPLOAD_FOLDER, str(file_id)) #NEEDS_TESTING
                render_result_file.save(file_path)

                file_size = os.path.getsize(file_path)
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                cursor.execute("UPDATE File SET Path=?, Size=?, Date=?, Hash=?, IsDeleted=?, Name=? WHERE ID=?",
                               (file_path, file_size, datetime.now(), file_hash, False, file_name,file_id))
                """
                cursor.execute('''
                    INSERT INTO File (Path, Size, Date, Hash, IsDeleted, Name)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (file_path, file_size, datetime.now(), file_hash, False, file_name))
                """


                
                cursor.execute("UPDATE RenderResult SET End = DATETIME('now'),File=? WHERE id=?", (file_id,RRid))

                #here it is. начисление токенов  #NEEDS_TESTING
                

                #accuire len of current RR
                #acquire node benchmark
                #multilpy lenofRR by NODE_BENCHMARK_SCORE

                cursor.execute("SELECT * FROM RenderResult WHERE ID=?",(RRid,))
                RRrow = cursor.fetchone()

                st = RRrow['Start']
                nd = RRrow['End']

                st =int( time.mktime(datetime.strptime(st, "%Y-%m-%d %H:%M:%S").timetuple()))
                nd =int( time.mktime(datetime.strptime(nd, "%Y-%m-%d %H:%M:%S").timetuple()))
                
                RRtime = nd-st

                
                cursor.execute("SELECT * FROM NodeBenchmark WHERE Node=? ORDER BY ID DESC", (id,))
                NodeBenchmark = cursor.fetchone()

                NodeBenchmark = NodeBenchmark['Benchmark']

                points = RRtime * NodeBenchmark
                print("NODE ", id, ' awarded ', points, " points for RR ", RRid)
                cursor.execute("UPDATE RenderResult SET Tokens=? WHERE ID=?",(points,RRid))
                pass;#debug


                """cursor.execute('''
                UPDATE RenderResult
                SET Tokens = (
                    SELECT ROUND(
                        (JULIANDAY(End) - JULIANDAY(Start)) * 86400  -- Time diff in seconds
                        * ? --coefficiento
                    )
                    FROM Node n
                    WHERE n.id = RenderResult."Node"
                )
                WHERE Start IS NOT NULL AND End IS NOT NULL AND ID=? 
            ''', (69,id))
                """
                

                # вычистать хэшь
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                #update file entry
                cursor.execute('''
                            UPDATE File SET Path=?, Size=?, Hash=? WHERE ID=?
                            ''', (file_path, os.path.getsize(file_path), file_hash, file_id))
                conn.commit()

    else:
        #logick for when NOT RENDER RESULT NEEDS_TESTING

        
        
    
        cursor.execute("SELECT * FROM RenderResult WHERE Node=? AND End IS NULL", (id,))
        rr = cursor.fetchone()


        taskID = None
        if rr is not None:
            taskID = rr['ID']  # Get the ID from the row directly
            
            task_proj_id = rr['Project']
            method_sep = rr['Info']
            
            #convert task_proj_id into FILE_ID you stupid fuck !!!
            cursor.execute("SELECT * FROM Project WHERE ID=?",(task_proj_id,))
            ASLKDASLKFALSDzdfzdxcz= cursor.fetchone()
            project_file_id =  ASLKDASLKFALSDzdfzdxcz['File']

            #set the start
            cursor.execute("UPDATE RenderResult SET Start=DATETIME('now') WHERE ID=?", (taskID,))
            
            cursor.execute("SELECT * FROM Project WHERE ID=?", (task_proj_id,))
            proj_file = cursor.fetchone()



            if proj_file is None:
                return jsonify({"status": "Project not found"})

            cursor.execute("SELECT * FROM Asset WHERE Project=?", (task_proj_id,))
            assets = cursor.fetchall()

            #files_id = [task_proj_id]
            files_id = [project_file_id]
            for asset in assets:
                files_id.append(asset['File'])

            form_filetable = []
            for x in files_id:
                cursor.execute("SELECT * FROM File WHERE id=?", (x,))
                y = cursor.fetchone()
                if y:
                    form_filetable.append({"name": y['name'], "hash": y['hash']})

            proj_name_sent = form_filetable[0]#add the name of the project here

            cursor.execute("UPDATE Node SET state=? WHERE ID=?", (const_nodestate_sent, id))
            tsk = taskID;

    conn.commit()
    conn.close()
    return jsonify({
        'status': "ok",
        'id': id,
        'wrk_sep_method': method_sep,
        'files_update': form_filetable,
        'task': tsk,#render result ID
        'project_name': proj_name_sent #project name to be inserted into commandline
    })

"""
    #SCAN RENDER RESULT WITHOUT END AND 
    cursor.execute("SELECT * FROM RenderResult WHERE Node=? AND End IS NULL", (id,))
    
    rr = cursor.fetchone()

    print("RR DEBUG ==== " + str(rr))
    
    taskID = cursor.lastrowid
    if rr is not None:
        task_proj_id = rr['Project']
        cursor.execute("SELECT * FROM Project WHERE ID=?", (task_proj_id,))
        proj_file = cursor.fetchone()
        proj_file_id = proj_file['File'] #main project file
        cursor.execute("SELECT * FROM Asset WHERE Project=?", (task_proj_id,))
        assets = cursor.fetchall()
        ass_file_id_arr=[]
        for ass in assets:
            ass_file_id_arr.append(ass['File'])


        files_id = []
        files_id.append(task_proj_id)
        for x in ass_file_id_arr : files_id.append(x)


        form_filetable=[]
        #fetch all hashsums and filenames
        for x in files_id:
            cursor.execute("SELECT * FROM File WHERE id=?",(x,))
            y = cursor.fetchone()
            form_filetable.append({"Name":y['Name'],"hash":y['Hash']} )

        form_filetable = json.dump(form_filetable)#no?

        launch_args = "uh"#blender launch args

        tsk = json.dumps({'id':taskID, 'project_file_hash': proj_file['hash']} );
    
        #setting state to sent
        cursor.execute("UPDATE Node SET state=? WHERE ID=?", (const_nodestate_sent, id))


    #bolierplate exit from function and response
    conn.commit()
    return jsonify({'status': "ok", 
                    "id":id, 
                    "files_update":form_filetable,
                    "task":tsk})


                    """


\













@app.route('/download/<fhash>/<fname>')
def api2DL(fhash, fname):
    try: 
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT Path FROM File WHERE name = ? AND hash = ?', (fname, fhash))
        result = cursor.fetchone()
        conn.close()
        fpath = result[0]
        file_path = os.path.join(fpath)
        #return send_file(file_path,as_attachement=True)
        return send_file(file_path)
    except: 
        conn.close() #just in case BS happens release database



















if __name__ == "__main__":
    print("i are server 2")
    init()

    #t = threading.Thread(target= algo)
    t = threading.Thread(target= algo_v2_frameSplit)
    t.start()



    app.run(host='127.0.0.1', port=6969)

    t.join()