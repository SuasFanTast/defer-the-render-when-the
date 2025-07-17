import requests
import threading
from time import sleep
import os
import hashlib
import json
import subprocess





CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """Load config from file or create with defaults"""
    if not os.path.exists(CONFIG_PATH):
        # Create default config with hardware info and paths
        default_config = {
            "blender_paths": ["/home/sergei/New Folder/bilshut_Locale/~~Spring2025/DB/ExperimentV3/Node/blender-4.4.3-linux-x64/blender"],
            "capabilities": {
                "program": "blender",
                "program_ver": "3.6",
                "plugin": "cycles",
                "plugin_ver": "1.0",
                "cpu": "Intel i7-13700K",
                "cpu_speed": "3.6",
                "cpu_cores": "16",
                "gpu": "NVIDIA RTX 4090",
                "vram": "24",
                "ram": "64",
                "free_space": "500",
                "cycles_device": "CPU",  # Default to CPU
                "threads": "12"       # Default threads (0 = auto)
            }
        }
        with open(CONFIG_PATH, 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)


config = load_config() #load that sucker


blender_paths = config["blender_paths"]
HARDWARE_CONFIG = config["capabilities"]










class Client:
    def __init__(self, host='http://127.0.0.1:6969'):
        self.host = host
        self.id = -1 #Because i said so
        self.rendering_proj_id = -1 

        self.result_filename = None

        DN = os.path.dirname( __file__)
        alpha = os.path.join(DN,'data')
        self.dir = (alpha) #
        os.makedirs(self.dir, exist_ok=True)

        """
        # Node capabilities and hardware info
        self.capabilities = {
            'program': 'blender',
            'program_ver': '3.6',
            'plugin': 'cycles',
            'plugin_ver': '1.0',
            'cpu': 'Intel i7-13700K',
            'cpu_speed': '3.6',
            'cpu_cores': '16',
            'gpu': 'NVIDIA RTX 4090',
            'vram': '24',
            'ram': '64',
            'free_space': '500'
        }
        """
        # Load capabilities from config file
        self.capabilities = HARDWARE_CONFIG.copy()
        # Available files metadata
        self.files_metadata = [
            #{'hash': 'abc123', 'name': 'scene.blend', 'size': '100MB'},
        ]
        self.files_metadata_received=[
            #{'hash': 'abc123', 'name': 'scene.blend', 'size': '100MB'}
        ]
        self.refresh_metadata()
        # Node status
        self.status = {
            'rendering': False,
            'current_task': None
        }

    def exchange(self, result_file=None, task_info=None):
        """Main communication loop with server"""
        # Prepare form data
        data = {
            'id': self.id,
            'ping': '1',  # Keep node online
            # Hardware info
            'cpu': self.capabilities['cpu'],
            'cpu_speed': self.capabilities['cpu_speed'],
            'cpu_cores': self.capabilities['cpu_cores'],
            'gpu': self.capabilities['gpu'],
            'vram': self.capabilities['vram'],
            'ram': self.capabilities['ram'],
            'free_space': self.capabilities['free_space'],
            # Software info
            'program': self.capabilities['program'],
            'program_ver': self.capabilities['program_ver'],
            'plugin': self.capabilities['plugin'],
            'plugin_ver': self.capabilities['plugin_ver'],
            # File metadata
            'files': json.dumps(self.files_metadata), #available files, put in node_file later
            'state':self.status
        }
        
        # Add task result data if available
        if task_info and result_file:
            data.update({
                #'proj_id': task_info['id'],
                'render_time': task_info['time'],
                'RRid':task_info['id'],
                'finished':'ok',
                'result_filename' : os.path.basename(result_file)#NEEDS_TESTING
            })
            
        # Prepare file upload
        files = {}
        if result_file:
            try:
                ##render_folder=os.listdir(os.path.join(self.dir,"renders"))  #before
                #files['result'] = open(os.path.join(self.dir,"renders",render_folder[0]), 'rb') ##before

                result_path = os.path.join(self.dir, "renders", self.result_filename)
                if os.path.isfile(result_path):
                    files['result'] = open(result_path, 'rb')

                """
                files_ = [f for f in render_folder if os.path.isfile(os.path.join(self.dir, f))]
                if files_:
                    # Construct the full path to the first file
                    file_path = os.path.join(self.dir, files_[0])
                    files['result'] = open(file_path, 'rb')
                """
            except Exception as e:
                print(f"Error opening result file: {e}")
                return None

        try:
            response = requests.post(
                f"{self.host}/api2",
                data=data,
                files=files if files else None
            )
            
            res_json = response.json()
            print("Server response:", res_json)
            
            
            if res_json['id'] != self.id:
                self.id = res_json['id']

            # Handle any files update, 
            if 'files_update' in res_json:
                self.files_metadata_received = res_json['files_update']
                
            
            return res_json
            
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            return {'error': str(e)}
        finally:
            # Close file if opened
            if files:
                files['result'].close()



    def start(self):
        """Start node main loop"""
        print(f"Node started with ID: {self.id}")
        
        # Initial registration
        #self.exchange()
        
        # Main loop
        while True:
            try:
                # Check for tasks and report status
                response = self.exchange()
                self.refresh_metadata()
                if self.find_missing_files():
                    self.download_missing_files()
                
                
                # Simulate task processing
                if 'task' in response:
                    if (response['task'] is not None):
                        #try:
                        if True:
                            #task_info = self.process_task(response['task'],response['project_name'],{integer shoud be here})
                            task_info = "ASS"
                            if response['wrk_sep_method'] == "benchmark":
                                task_info = self.process_task(response['task'],response['project_name'],0)
                            else:
                                wrk_sep_method = json.loads(response['wrk_sep_method'])
                                task_info = self.process_task(response['task'],response['project_name'],wrk_sep_method['framestart'])

                        #except Exception:
                        if False:    
                            self.exchange(task_info={'error':'error'})

                        # Upload result after processing
                        self.exchange(
                            #result_file=(task_info['name']),
                            result_file=self.result_filename,
                            task_info=task_info
                        )
                
                # Wait before next ping
                sleep(7)
            except KeyboardInterrupt:
                print("Shutting down node...")
                break

    def process_task(self, task,proj_name, frame):
        """Simulate task processing"""
        
        self.rendering_proj_id = task

        #RENDER HERE
        output_file = "renders"
        output_path = os.path.join(self.dir, output_file)
        os.makedirs(output_path, exist_ok=True)

        self.result_filename = "temp001_new"
        result_path = os.path.join(output_path, self.result_filename)

        result_info = {
            'id': task,
            'time': '30s',
            'name': self.result_filename
        }



        print("Processing task:", task)
        self.status['rendering'] = True
        self.status['current_task'] = task
        

        #NEEDS_TESTING
        self.result_filename = self.launch_blender_render(str(os.path.join(self.dir,proj_name['name'])), result_path, frame)

   

        #runcommand = '"'+blender_paths[0]+'" -t 10 ' + "  -b   " + '"'+os.path.join(self.dir,proj_name['name'])+'"' + " -o " + '"'+ output_path +'/"' + "    -f 3  "  
        
        #os.system(runcommand)#launch blender and enjoy CPU meltdown


        """
        with open(os.path.join(output_path, "temp001"), 'w') as a:
            a.writelines("bruh,temp render")
            a.close
"""
            

        # Update files metadata
        
        
        
        #result_hash = hashlib.sha256(output_file.encode()).hexdigest()
        result_hash = self._compute_file_hash(self.result_filename)
        
        """
        self.files_metadata.append({
            'hash': result_hash,
            'name': output_file,
            'size': '10MB',
            'log_raw': 'here is the blender log raw file'
        })
        """
        self.files_metadata.append({
            'hash': result_hash,
            'name': self.result_filename,
            'size': f"{os.path.getsize(self.result_filename)}B",
            'log_raw': 'here is the blender log raw file'
        })


        
        
        
        """
        result_info = {
            'id': task,
            'time': '30s',
            'name': output_path
        }
        
        """
        self.status['rendering'] = False
        self.status['current_task'] = None
    
        return result_info
    

    def launch_blender_render(self, blend_file, output_path, frame):
        """
        Launch Blender render and capture the saved file path.
        
        Args:
            blend_file (str): Path to the .blend file
            output_path (str): Output directory for rendered frames
        
        Returns:
            str: Path to the saved rendered image
        """
        # Set Blender's output path via command line args
        command = [
            blender_paths[0], 
            "--background", 
            #'"',
              blend_file, 
             # '"',
            "--render-output", 
            #'"',
              output_path,
               # '"',
            "--render-frame", str(frame),  # or "--render-frame" for single frame
            #" --render-frame"
            #"-a"
            "--cycles-device", HARDWARE_CONFIG["cycles_device"],
            "--threads", HARDWARE_CONFIG["threads"]
        ]

        print("%%", command)
        
        # Capture both stdout and stderr (Blender sometimes uses stderr!)
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        saved_path = None
        
        # Read output line by line
        while True:
            line = process.stdout.readline()
            print("%",line)
            if not line:
                break
            
            # Look for Blender's save message
            if line.startswith("Saved: '"):
                # Extract path between quotes
                saved_path = line.strip()[8:-1]
                print(f"✨ Captured saved path: {saved_path}")
        
        # Wait for process to complete
        process.wait()
        
        return saved_path

    def refresh_metadata(self):
        data_dir = self.dir  # ✅ Simplified
        print(f"Scanning directory: {data_dir}")  # 🔍 Debugging

        self.files_metadata.clear()

        if not os.path.isdir(data_dir):
            raise ValueError(f"The directory '{data_dir}' does not exist.")

        for root, dirs, files in os.walk(data_dir):
            #print(f"Current directory: {root}")  # 🧪 Debugging
            #print(f"Subdirectories: {dirs}")     # 🧪
            #print(f"Files found: {files}")       # 🧪

            for filename in files:
                file_path = os.path.join(root, filename)
                try:
                    file_size = os.path.getsize(file_path)
                    file_hash = self._compute_file_hash(file_path)
                    self.files_metadata.append({
                        'hash': file_hash,
                        'name': filename,
                        'size': f"{file_size}B"
                    })
                except Exception as e:
                    print(f"Error processing file {file_path}: {e}")


    def download_missing_files(self):
        download_dir = self.dir
        """Download missing files by their IDs."""
        missing_files= self.find_missing_files()
        for file_info in missing_files:
            file_name = file_info['name']
            file_hash = file_info['hash']
            download_url = f'http://localhost:6969/download/{file_hash}/{file_name}'
            print(f"Downloading {file_name} ...")
            try:
                response = requests.get(download_url, stream=True)
                if response.status_code == 200:
                    with open(os.path.join(download_dir, file_name), 'wb') as f:
                        for chunk in response.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)
                    print(f"Saved {file_name}")
                else:
                    print(f"Failed to download {file_name}")
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")

    def _compute_file_hash(self, file_path, hash_algorithm='md5'):
        hash_obj = getattr(hashlib, hash_algorithm)() #for the times when md5 is not gonna be enough for some reason
        with open(file_path, 'rb') as file:
            while chunk := file.read(4096):  # Read file in chunks
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    


    def find_missing_files(self): 
        client_metadata = self.files_metadata
        server_metadata = self.files_metadata_received
        """Find files that the client is missing."""
        client_hashes = {(f['name'], f['hash']) for f in client_metadata}
        missing = []
        if server_metadata:
            for file in server_metadata:
                key = (file['name'], file['hash'])
                if key not in client_hashes:
                    missing.append(file)
            if len(missing) != 0:
                return missing
        return None
        

if __name__ == "__main__":
    print("Starting distributed rendering node")
    client = Client()
    client.start()

