import requests
import json
import hashlib
from datetime import datetime

class Client:
    def __init__(self, host='http://127.0.0.1:5000'):
        self.host = host

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

    def register(self, username, password):
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('register', data=data)

    def login(self, username, password):
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('login', data=data)

    def stats(self, username, password):
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('stats', data=data)

    def add_asset(self, username, password, filename, file_path, project_name):
        files = {
            'file': (filename, open(file_path, 'rb'))
        }
        data = {
            'username': username,
            'password': password,
            'filename': filename,
            'project_name': project_name
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

    def run_project(self, username, password, project_name):
        data = {
            'username': username,
            'password': password,
            'project_name': project_name
        }
        return self._make_request('run', data=data)

    def delete_asset(self, username, password, asset_name):
        data = {
            'username': username,
            'password': password,
            'asset_name': asset_name
        }
        return self._make_request('delete_asset', data=data)

    def delete_project(self, username, password, project_name):
        data = {
            'username': username,
            'password': password,
            'project_name': project_name
        }
        return self._make_request('delete_project', data=data)

    def download_render_result(self, username, password, project_name):
        data = {
            'username': username,
            'password': password,
            'project_name': project_name
        }
        return self._make_request('download_render_result', data=data)

    def add_node(self, username, password):
        data = {
            'username': username,
            'password': password
        }
        return self._make_request('add_node', data=data)

    def unlink_node(self, username, password, node_id):
        data = {
            'username': username,
            'password': password,
            'node_id': node_id
        }
        return self._make_request('unlink_node', data=data)

if __name__ == '__main__':
    client = Client()

    # Example registration
    print(client.register('user1', 'pass1'))
    print(client.register('user2', 'pass2'))

    # Example login
    print(client.login('user1', 'pass1'))

    # Example add project
    print(client.add_project('user1', 'pass1', 'test_project', 'test_project.txt'))

    # Example add asset
    print(client.add_asset('user1', 'pass1', 'test.txt', 'test.txt', "test_project"))

    # Example run project
    print(client.run_project('user1', 'pass1', 'test_project'))

    # Example delete asset
    print(client.delete_asset('user1', 'pass1', 'test.txt'))

    # Example delete project
    print(client.delete_project('user1', 'pass1', 'test_project'))

    # Example add node
    print(client.add_node('user1', 'pass1'))

    # Example unlink node
    # Get node_id from add_node response and use it here
    # print(client.unlink_node('user1', 'pass1', node_id))
