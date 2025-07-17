import json
import requests
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
from PIL import Image, ImageTk
from time import sleep
import os
import zipfile
import ast


#internal
username = ""
password = ""
isSuccess = False

proj_arr = any
ass_arr = any
node_arr = any

#ui_show
tokens = -1
nodeKey = 0; #USERID (hashed sha256)?
projects = [("",[])] #string of text with info, array of assets
assets = [""]
nodes = [""]

#NET CODE
class Client:
    def __init__(self, host='http://127.0.0.1:5000'):
            self.host = host
    def store_credentials(self,u,p):
        self.username = u
        self.password = p

    def _make_request(self, endpoint, method='POST', data=None):
        url = f"{self.host}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        try:
            if method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'GET':
                response = requests.get(url, headers=headers, params=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
        
    def add_project(self, username, password, project_name, file_path):
        files = {
            'file': open(file_path, 'rb')
        }
        data = {
            'username': username,
            'password': password,
            'project_name': project_name
        }
        try:
            response = requests.post(
                f"{self.host}/add_project",
                files=files,
                data=data
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
        
    def delete_project(self, username, password, project_name):
        data = {
            'username': username,
            'password': password,
            'project_name': project_name
        }
        return self._make_request('delete_project', data=data)
    
    def add_asset(self, username, password, filename, file_path, project_name=None):
        files = {
            #'file': (filename, open(file_path, 'rb'))
            'file':  open(file_path, 'rb')
        }
        data = {
            'username': username,
            'password': password,
            'filename': filename,
            #'project_name': project_name
        }
        try:
            response = requests.post(
                f"{self.host}/add_asset",
                files=files,
                data=data
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
        
    def delete_asset_byID(self, assetID):
        data={
            'username':self.username,
            'password':self.password,
            'assetID':assetID
        }
        return self._make_request('/delete_asset_byID', data=data)
        
    def bind_asset_to_project(self, username, password, project_name, asset_name, isUnbind=False):
        data = {
            'username':username,
            'password':password,
            'project':project_name,
            'asset':asset_name,
            'action':isUnbind
        }
        print("REQUEST FORM DEBUG __BIND_ASS__")
        print(data)
        return self._make_request('bind_asset_to_project', data=data)

    def start_proj(self, id):
        data = {
            'username':username,
            'password':password,
            'projId':id
        }
        return self._make_request('start_project', data=data)
    
    def bind_node(self, node_id):
        data = {
            'username':username,
            'password':password,
            'node_id':node_id
        }
        return self._make_request('add_node', data=data)
    
    def get_result(self,proj_id):
        data = {
            'username':username,
            'password':password,
            'proj_id':proj_id
        }
        return self._make_request('download_render_result', data=data)
    
    def DL(self,missing_files):
        DN = os.path.dirname( __file__)
        download_dir = os.path.join(DN,'Res_Download')
        os.makedirs(download_dir, exist_ok=True)
        for file_info in missing_files['files']:
            file_name = file_info['Name']
            file_hash = file_info['Hash']
            download_url = f'http://localhost:6969/download/{file_hash}/{file_name}'
            print(f"Downloading {file_name} ...")
            try:
                response = requests.get(download_url, stream=True)
                if response.status_code == 200:
                    file_path = os.path.join(download_dir, file_name)
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=4096):
                            if chunk:
                                f.write(chunk)
                    print(f"Saved {file_name}")
                else:
                    print(f"Failed to download {file_name}")
            except Exception as e:
                print(f"Error downloading {file_name}: {e}")
    

    def register(self, username, password):
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('register', data=data)
    
    
        
#===============











cl = Client()


def get_user_info():
    print("GET USER INFO DEBUG")
    global tokens, nodeKey, projects, assets, proj_arr, ass_arr, node_arr

    tokens = -1
    nodeKey = -1
    projects = []
    assets = []
    node_arr = []
    

    cl.store_credentials(username, password)

    res = cl._make_request('stats', data={
        'username':username,
        'password':password
    })

    nodeKey = res['user_id']

    #tokens = res['tokens'] shitass remember to deprectate

    #Project processing = 1st pass - all
    proj_arr = res.get('projects', [])
    count = 0

    for i in proj_arr:
        # "i" here is DICT!! BUT ONLY ON TUESDAYS!
        l = dict(i)
        #custom processing logick
        form_str = str(l.get('Name')) + "||" + str(l.get('ID')) + "||" + str(l.get('Size')) + "||" + str(l.get("Program")) + "||" + str(l.get("RenderResult"))
        projects.append((form_str, []))
        count+=1

    #print(projects)#debug print are always fun
    print("====ALLFILES====",res['files'])


    #old assets forming code all janky-wise
    
    ass_arr = res.get('assets',[])
    print("===333===",ass_arr)
    form_str=""
    for i in ass_arr:
        l=dict(i)
        print("DEBUG_PREPROCESSOR",l)
        #form_str = filter(lambda x: x.get('ID')==l.get('Project'), proj_arr)
        


        file_id = l.get('File')
        file_info = next((file for file in res.get('files', []) if file.get('ID') == file_id), None)
        if file_info:
            file_name = file_info.get('Name')
            file_size = file_info.get('Size')
            file_date = file_info.get('Date')
            if file_date:
                file_date = file_date.split('.')[0]  # Remove decimal seconds
        
        
        for pr in proj_arr:
            if (pr.get('ID') == l.get('Project')):
                pass
                #print(l)
                #form_str = str((pr.get("Name")) + "||" + str(pr.get("ID")) + "||" + str(l.get("ID")) + "||" )
                form_str = str(file_name + "||" + str(pr.get("Name")) + "||" + str(file_size) + "||" + file_date + "||" + str(pr.get("ID")) )
        assets.append(form_str)

        print(l)
        print(form_str)
    




    node_lal = res.get('nodes')
    form_str = ""
    #print(node_lal)
    node_lal = json.loads(node_lal)
    global nodes
    nodes = [""]
    for i in node_lal:
        form_str = str(i)
        nodes.append(form_str)
    #nodes.append("==bruh string debug!!==")
    #nodes = ["=THE HAD ASS DEBUG PLEASE DEBUG DEBUG==", "ASS2", "ASSDSSSSSSS3"]


    #print(res)














#login window
class LoginForm(tk.Tk):
    def __init__(self):
        global cl
        
        super().__init__()
        
        self.title("LOIGN")
        self.geometry("800x450")
        
        # Create UI components
        self.create_widgets()

        
    
    def create_widgets(self):
        # Image handling - replace 'logo.png' with your actual image path
        try:
            image = Image.open("logo.png")
            image = image.resize((274, 177), Image.LANCZOS)
            self.logo_image = ImageTk.PhotoImage(image)
            
            self.label_logo = tk.Label(self, image=self.logo_image)
            self.label_logo.place(x=274, y=47)
        except FileNotFoundError:
            print("image not found. Too bad! i dont have time for this rn.")
        
        # Labels
        self.label_login = ttk.Label(self, text="Логин")
        self.label_login.place(x=253, y=255)
        
        self.label_password = ttk.Label(self, text="Параль")
        self.label_password.place(x=256, y=324)
        
        # Entry fields
        self.entry_login = ttk.Entry(self)
        self.entry_login.place(x=313, y=250, width=209)
        
        
        self.entry_password = ttk.Entry(self, show="*")  # Mask password input
        self.entry_password.place(x=313, y=319, width=209)
        
        
        # Buttons
        self.btn_login = ttk.Button(self, text="вход", command=self.button_login_click)
        self.btn_login.place(x=313, y=381, width=75)
        
        self.btn_register = ttk.Button(self, text="регистрация", command=self.button_register_click)
        self.btn_register.place(x=410, y=381, width=112)
    
    # Event handlers
    def button_login_click(self):
        print("Вход clicked")



        global username, password


        username = self.entry_login.get()
        password = self.entry_password.get()



#        username = "user1"
#        password = "pass1"

        response = cl._make_request('login', data=
        {
            'username': username,
            'password': password
        })

        print(username + "  " +  password)
        try:
            if(response['error']):
                messagebox.showerror(title="ошибка", message=str(response['error']) + "пытайтесь ещё раз или позже")
        except Exception as e:
            print(response)
        
        #populate variables over here with separate update stats func before showing the main ui

        if (response['status'] == "ok"):

            self.destroy()
            global isSuccess
            isSuccess = True
        
    
    def button_register_click(self):

        global username, password


        username = self.entry_login.get()
        password = self.entry_password.get()


        cl.register(username,password)
        print("Регистрация clicked")
        self.destroy()
#================


#Beauiful main TK interface 
class MyApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Defer the render when the ")
        self.geometry("1104x490")
        
        # Create tab control
        self.tab_control = ttk.Notebook(self)
        
        # Create tabs
        self.tab_projects = ttk.Frame(self.tab_control)
        self.tab_machines = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_projects, text="мои проекты")
        self.tab_control.add(self.tab_machines, text="мои узлы")
        self.tab_control.pack(expand=1, fill="both")

        self.current_project_id = None
        self.filter_assets_var = tk.BooleanVar()
        
        # Initialize UI components
        self.init_projects_tab()
        self.init_machines_tab()


        self.after(0, self.refresh_ui)  #обновляем юи, но зачем???
    
    def init_projects_tab(self):
        # Labels
        """
        self.label_balance = ttk.Label(self.tab_projects, text="Баланс токенов:")
        self.label_balance.place(x=6, y=13)
        
        self.tokens_label = ttk.Label(self.tab_projects, text="tokenlabelblelnell")
        self.tokens_label.place(x=128, y=13)
        """

        #old buttonas :shrimp:
        
        # Buttons
        self.btn_add_project = ttk.Button(self.tab_projects, text="𐊨 проект", command=self.button_add_project_click)
        self.btn_add_project.place(x=6, y=59, width=84, height=63)
        
        self.btn_update_project = ttk.Button(self.tab_projects, text="𐋇 проект", command=self.button_update_project_click)
        self.btn_update_project.place(x=96, y=59, width=84, height=63)
        
        self.btn_delete_project = ttk.Button(self.tab_projects, text="𐊴 проект", command=self.button_delete_project_click)
        self.btn_delete_project.place(x=186, y=59, width=84, height=63)
        
        self.btn_start_render = ttk.Button(self.tab_projects, text="!пуск!", command=self.button_start_render_click)
        self.btn_start_render.place(x=336, y=59, width=88, height=63)
        
        self.btn_download = ttk.Button(self.tab_projects, text="𐠮 результат", command=self.button_download_click)
        self.btn_download.place(x=430, y=59, width=88, height=63)

        self.btn_bind = ttk.Button(self.tab_projects, text="𛱘 ассет", command = self.button_bind_asset)
        self.btn_bind.place(x=650, y=59, width=84, height = 63)
        
        self.btn_add_asset = ttk.Button(self.tab_projects, text="𐊨 ассет", command=self.button_add_asset_click)
        self.btn_add_asset.place(x=788, y=59, width=84, height=63)
        
        self.btn_update_asset = ttk.Button(self.tab_projects, text="𐋇 ассет", command=self.button_update_asset_click)
        self.btn_update_asset.place(x=878, y=59, width=84, height=63)
        
        self.btn_delete_asset = ttk.Button(self.tab_projects, text="𐊴 ассет", command=self.button_delete_asset_click)
        self.btn_delete_asset.place(x=968, y=59, width=84, height=63)
        
        
        """ #refersh button for advanced begugging!!
        self.btn_refresh_view = ttk.Button(self.tab_projects, text = "обновить", command=self.refresh_ui)
        self.btn_refresh_view.place(x=500, y=10, width=100, height=40)
        """

        """
        self.btn_add_project = ttk.Button(self.tab_projects, text="добавить проект", 
                                   command=self.button_add_project_click, 
                                   wraplength=84)
        self.btn_add_project.place(x=6, y=59, width=84, height=63)

        self.btn_update_project = ttk.Button(self.tab_projects, text="обновить проект", 
                                            command=self.button_update_project_click, 
                                            wraplength=84)
        self.btn_update_project.place(x=96, y=59, width=84, height=63)

        self.btn_delete_project = ttk.Button(self.tab_projects, text="удалить проект", 
                                            command=self.button_delete_project_click, 
                                            wraplength=84)
        self.btn_delete_project.place(x=186, y=59, width=84, height=63)

        self.btn_start_render = ttk.Button(self.tab_projects, text="!пуск!", 
                                        command=self.button_start_render_click, 
                                        wraplength=88)
        self.btn_start_render.place(x=336, y=59, width=88, height=63)

        self.btn_download = ttk.Button(self.tab_projects, text="Скачать результат", 
                                    command=self.button_download_click, 
                                    wraplength=88)
        self.btn_download.place(x=430, y=59, width=88, height=63)

        self.btn_bind = ttk.Button(self.tab_projects, text="связать асс", 
                                command=self.button_bind_asset, 
                                wraplength=84)
        self.btn_bind.place(x=650, y=59, width=84, height=63)

        self.btn_add_asset = ttk.Button(self.tab_projects, text="добавить ассет", 
                                        command=self.button_add_asset_click, 
                                        wraplength=84)
        self.btn_add_asset.place(x=788, y=59, width=84, height=63)

        self.btn_update_asset = ttk.Button(self.tab_projects, text="обновить ассет", 
                                        command=self.button_update_asset_click, 
                                        wraplength=84)
        self.btn_update_asset.place(x=878, y=59, width=84, height=63)

        self.btn_delete_asset = ttk.Button(self.tab_projects, text="удалить ассет", 
                                        command=self.button_delete_asset_click, 
                                        wraplength=84)
        self.btn_delete_asset.place(x=968, y=59, width=84, height=63)
        """


        #850 100

        #self.checkbox_filterass = ttk.Checkbutton(text="отфильтровать асс по проэктам", command= self.checkbox_changed)
        self.checkbox_filterass = ttk.Checkbutton(text="фильтр асс. по проектам",variable=self.filter_assets_var, 
            command=self.checkbox_changed)
        
        self.checkbox_filterass.place(x=850, y=50, width=200, height=25)

        # List boxes
        self.label_projects = ttk.Label(self.tab_projects, text="Проект")
        self.label_projects.place(x=216, y=134)
        
        self.listbox_projects = tk.Listbox(self.tab_projects, selectmode='browse', exportselection=False)
        self.listbox_projects.insert(tk.END, "[FileName] [Weight] [Версия] [состояние] [[примерно осталось]]")
        self.listbox_projects.place(x=3, y=153, width=515, height=260)
        self.listbox_projects.bind("<<ListboxSelect>>", self.on_project_select)
        
        self.label_asset = ttk.Label(self.tab_projects, text="Ассет")
        self.label_asset.place(x=772, y=134)
        
        self.listbox_assets = tk.Listbox(self.tab_projects, selectmode='browse', exportselection=False)
        self.listbox_assets.insert(tk.END, "[галачка] [FileName] [Weight] [Версия]")
        self.listbox_assets.place(x=537, y=153, width=515, height=260)
    
    def init_machines_tab(self):
        self.label_key = ttk.Label(self.tab_machines, text="ключъъъъъ:")
        self.label_key.place(x=6, y=22)
        
        self.listbox_machines = tk.Listbox(self.tab_machines)
        self.listbox_machines.insert(tk.END, "[машина] [cpu/gpu] [версии блндра] [первормансе (сэмпл/мин)] [токенов/час] [свободно места]")
        self.listbox_machines.place(x=4, y=75, width=1062, height=340)

        self.button_bind = ttk.Button(self.tab_machines, text="привязать узел", command=self.bind_node)
        self.button_bind.place(x=180, y=5, width=100, height=50)
    
    # Event handlers - placeholders
    def button_add_project_click(self):
        print("Добавить проект clicked")
        #print(messagebox.showinfo(title="Adding a project", message="adding a project"))
        filename = filedialog.askopenfilename(initialdir = "/",
                                          title = "Выберите файл",
                                          filetypes = (("Файлы Blender",
                                                        "*.blend*"),
                                                       ("все файлы",
                                                        "*.*")))
        
        item = simpledialog.askstring("Новый проект!", "Обзовите его:")
        print(item)

        print(filename)

        def bruh():
            print("bruh")

    
        resp = cl.add_project(username, password, item, filename)

        print(str(resp))
        self.refresh_ui()
        """
        files = {
            'file': open(filename, 'rb')
        }
        data={
            'username' : username,
            'password' : password,
            'project_name' : item
        }
        """

        
        
        
    
    def button_update_project_click(self):
        print("Обновить проект clicked")
    
    def button_delete_project_click(self):
        print("Удалить проект clicked")
        
        selected = self.listbox_projects.get( self.listbox_projects.curselection())

        proj_name = selected.split("||")[0]
        if selected:
            res = cl.delete_project(username,password,proj_name)
        
        #print(str(res)+ "   " + proj_name + " 09090 " + str(selected))
    
    def button_start_render_click(self):
        selected = str(self.listbox_projects.get(self.listbox_projects.curselection()))
        BuTT = self.listbox_projects.curselection()[0]
        res = cl.start_proj(proj_arr[BuTT - 1 ]['ID'])
        print(res)
        print("ПУСК clicked")
        self.refresh_ui()
    
    def button_download_click(self):
        selected = str(self.listbox_projects.get(self.listbox_projects.curselection()))
        BuTT = self.listbox_projects.curselection()[0]
        #res = cl.start_proj(proj_arr[BuTT - 1 ]['ID'])

        print(cl.DL(cl.get_result(proj_arr[BuTT - 1 ]['ID'])))
        #cl.download_and_extract(selected.split("||")[1])
        #cl.get_RR(selected.split("||")[1])
        print("Скачать результат clicked")
        self.refresh_ui(self)
    

    def button_add_asset_click(self):
        
        filename = filedialog.askopenfilename(
            initialdir="/",
            title="Выберите файл",
            filetypes=(("Файлы Blender", "*.blend*"), ("все файлы", "*.*"))
        )
    
        if not filename:
            return  # Exit if the user cancels the file selection

        # Automatically generate item name from the filename 
        item = os.path.basename(filename)
        
        #resp = cl.add_project(username, password, item, filename)
        resp = cl.add_asset(username, password, item,filename)

        print(str(resp))

        
    
        selected = self.listbox_projects.get( self.listbox_projects.curselection())
        sleep(10)
        proj_name = selected.split("||")[0]
        result = cl.bind_asset_to_project(username, password, proj_name, item)
        print(result)
        print("Добавить ассет clicked")
        self.refresh_ui()
    
    def button_bind_asset(self):
        print ("свяхать БИНЖ батон кликед")
        
        print("Projects selected:", self.listbox_projects.curselection())
        print("Assets selected:", self.listbox_assets.curselection())
        
        
        # Get selected indices
        selected_projects = self.listbox_projects.curselection()
        selected_assets = self.listbox_assets.curselection()

        # Ensure one item is selected in each listbox
        if not selected_projects or not selected_assets:
            print("Please select one project and one asset.")
            return

        # Get the selected items
        project_item = self.listbox_projects.get(selected_projects[0])
        asset_item = self.listbox_assets.get(selected_assets[0])

        # Extract the project name and asset name (assuming fields are split by '||')
        project_name = project_item.split("||")[0]
        asset_name = asset_item.split("||")[0]  # FIRST field assumed to be asset name

        # Call the bind function with the selected project and asset
        result = cl.bind_asset_to_project(username, password, project_name, asset_name)
        print("Binding result:", result)

        # Refresh the UI to reflect the change
        self.refresh_ui()

    def button_update_asset_click(self):
        print("Обновить ассет clicked")
        self.refresh_ui()
    
    def button_delete_asset_click(self):
        print("====")
        selected = str(self.listbox_assets.get(self.listbox_assets.curselection()))
        selected = selected.split("||")[2]
        print(selected)
        res = cl.delete_asset_byID(selected)
        print(res)
        print("Удалить ассет clicked")
        self.refresh_ui()

    def refresh_ui(self):

        get_user_info()



        self.listbox_projects.delete(0,tk.END)
        #self.listbox_projects.insert(tk.END, "[FileName] [Weight] [Версия] [состояние] [[примерно осталось]]")
        #self.listbox_projects.insert(tk.END, "    Имя    | id |   Размер   |  программа    |  результат")
        self.listbox_projects.insert(tk.END, "    Имя    |   Размер   |  программа    |  результат")
        for i in projects:
            print("Actual stuff that gets shoved into UI ==== ", i[0])
            #self.listbox_projects.insert(tk.END, i[0])
            parts = i[0].split("||")
            program = parts[3] if parts[3] != "1" else "Blender"
            modified = f"{parts[0]}||{parts[2]}||{program}||{parts[4]}"
            self.listbox_projects.insert(tk.END, modified)

        

        #self.tokens_label['text'] = "Токенов: " + str(tokens)
        """ #OLD CODE but works
        self.listbox_assets.delete(0,tk.END)
        self.listbox_assets.insert(tk.END, "[галачка] [FileName] [Weight] [Версия]")
        for i in assets:
            print("LISTBOX assets DEBUG==", i)
            self.listbox_assets.insert(tk.END, i)

            
        """

        #old ass code
        self.listbox_assets.delete(0, tk.END)
        
        #self.listbox_assets.insert(tk.END, "[галачка] [FileName] [Weight] [Версия]")
        self.listbox_assets.insert(tk.END, "Имя | Проект | Размер | Дата")

        if self.filter_assets_var.get() and self.current_project_id is not None:
            for asset in assets:
                parts = asset.split("||")
                if len(parts) >= 2 and parts[-1] == self.current_project_id:
                    self.listbox_assets.insert(tk.END, asset)
        else:
            for asset in assets:
                self.listbox_assets.insert(tk.END, asset)
        
        #end of old ass code


        ##new ass code

        """
        self.listbox_assets.delete(0, tk.END)
        for asset in assets:
            self.listbox_assets.insert(tk.END, asset)
        """


        ##end of new ass code


        """self.listbox_machines.delete(0,tk.END)
        for i in nodes:
            self.listbox_machines.insert(tk.END,i)
            print("UI_DEBUG == ", str(i))

        # old code b4 formatting    

            """
        

        # Clear the listbox before adding new content
        self.listbox_machines.delete(0, tk.END)

        # Define which keys to display and their human-readable labels
        display_columns = [
            ('HWConfig', 'HW Config'),
            ('SWConfig', 'SW Config'),
            ('FreeSpaceMB', 'Free Space (MB)'),
            ('BenchmarkResult', 'Benchmark Result'),
            ('LastPing', 'Last Ping'),
            ('State', 'State'),
        ]

        # Create and insert the header row
        header = " | ".join([label for key, label in display_columns])
        self.listbox_machines.insert(tk.END, header)

        # Process each string in the nodes list
        for node_str in nodes:
            try:
                # Safely convert the string to a dictionary
                node_dict = ast.literal_eval(node_str)

                # Format the row with only the selected keys
                row = []
                for key, label in display_columns:
                    value = node_dict.get(key, '')  # Get value, default to empty
                    row.append(str(value) if value is not None else '')  # Replace None with ''

                # Join the values into a formatted string and insert into listbox
                formatted_row = " | ".join(row)
                self.listbox_machines.insert(tk.END, formatted_row)
                print("UI_DEBUG == ", formatted_row)

            except (SyntaxError, ValueError) as e:
                # Handle malformed strings safely
                print(f"Error parsing node: {e}")
                #self.listbox_machines.insert(tk.END, "[Invalid Node Data]")

        self.label_key['text'] =  "key:" + str(nodeKey)

        print("UI refresh")
        #self.refresh_ui() #rooky mistake
        try:
            #self.after(3000, self.refresh_ui) #автообновление ынтрейеся
            pass
        except:
            pass    #в случае реурсия


    def bind_node(self):
        node_id = simpledialog.askstring(title="привязать узел", prompt='число:')
        #print(node_id)
        cl.bind_node(int(node_id))
        pass
        self.refresh_ui()



    #event handler woohoooo
    def on_project_select(self, event):
        if self.listbox_projects.curselection():
            """
            selected = self.listbox_projects.get(self.listbox_projects.curselection())
            parts = selected.split("||")
            if len(parts) >= 2:
                self.current_project_id = parts[1]
                """
            selectionIndex = self.listbox_projects.curselection()[0]
            parts = projects[selectionIndex-1][0].split("||")
            if len(parts) >= 2:
                self.current_project_id = parts[1]
            else:
                self.current_project_id = None
        else:
            self.current_project_id = None

        if self.filter_assets_var.get():
            self.refresh_ui()

    def checkbox_changed(self):

        self.refresh_ui()
#====================










if __name__ == "__main__":
    logingForm = LoginForm()
    logingForm.mainloop()
    if not isSuccess:
        quit()
    get_user_info()
    app = MyApplication()
    app.mainloop()