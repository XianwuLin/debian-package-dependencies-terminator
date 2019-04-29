# /usr/bin/env python
# -*- coding: utf-8 -*-
import glob
import logging
import os
import shutil
import tarfile
import tempfile

import docker
from flask import Flask, jsonify, request, send_file, abort

app = Flask(__name__)
port = 8765
download_folder = "./debs"


def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w") as tar:
        for fpath in glob.glob(os.path.join(source_dir, "*.deb")):
            tar.add(fpath, arcname=os.path.basename(fpath))


Docker_image_dict = {
    "ubuntu 16.04": "ubuntu1604:0.1.0"
}


@app.route('/api/dpdt/create', methods=['POST'])
def create():
    req = request.json
    system_version = req["system_version"]
    command = req["command"]
    tmp_folder = tempfile.mkdtemp()
    os.mkdir(os.path.join(tmp_folder, 'apt'))

    with open(os.path.join(tmp_folder, 'main.sh'), "w") as f:
        f.write(command.replace("\r\n", "\n"))

    client = docker.from_env()
    container = client.containers.run(Docker_image_dict[system_version],
                                      volumes={os.path.join(tmp_folder, 'apt/'): {'bind': '/var/cache/apt/archives/',
                                                                                  'mode': 'rw'},
                                               os.path.join(tmp_folder, 'main.sh'): {'bind': '/root/main.sh',
                                                                                     'mode': 'ro'}},
                                      detach=True)

    return jsonify({"status": 2000, "result": {"id": container.id}})


@app.route('/api/dpdt/status', methods=['GET'])
def status():
    container_id = request.args.get('id')
    client = docker.from_env()
    try:
        container = client.containers.get(container_id)
        if container.status == "exited":
            local_debs_path = ""
            for item in container.attrs["Mounts"]:
                if item["Destination"] == "/var/cache/apt/archives":
                    local_debs_path = item["Source"]
            if container.attrs["State"]["ExitCode"] != 0:
                # if return code is not zero, there must be some mistakes in command.
                result = {"status": 4001, "message": container.logs()}
                shutil.rmtree(os.path.dirname(local_debs_path))
                container.remove()
                return jsonify(result)
            else:
                # create finish, and create tar file
                if not local_debs_path:
                    return jsonify({"status": 4002, "message": "find debs folder error"})
                deb_tar_file_path = os.path.join(download_folder, container_id + ".tar")
                make_tarfile(deb_tar_file_path, local_debs_path)
                # clean container and tmp folder
                shutil.rmtree(os.path.dirname(local_debs_path))
                container.remove()
                return jsonify({"status": 2000, "message": "finish",
                                "result": {"path": '/api/dpdt/download?id=' + container_id}})
        elif container.status == "dead":
            # container dead
            return jsonify({"status": 4001, "message": container.logs()})
        else:
            # container is running and return logs
            return jsonify({"status": 2001, "message": "running", "result": {"logs": container.logs()}})
    except Exception as e:
        logging.exception(e)
        return jsonify({"status": 4000, "message": "id is unvalid"})


@app.route('/api/dpdt/download', methods=['GET'])
def download():
    container_id = request.args.get('id')
    deb_tar_file_path = os.path.join(download_folder, container_id + ".tar")
    if os.path.exists(deb_tar_file_path):
        return send_file(deb_tar_file_path, as_attachment=True)
    else:
        abort(404)


@app.route('/', methods=['GET'])
def index():
    return send_file('./index.html')


if __name__ == '__main__':
    app.run(port=port, host='0.0.0.0')
