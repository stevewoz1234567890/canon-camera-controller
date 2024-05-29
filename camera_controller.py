# This application uses the Canon CCAPI to control an EOS R5 camera

import requests
import json
from tqdm import tqdm
import os, sys, time, io
import PySimpleGUI as sg
from tkinter import *
from PIL import Image
from os.path import exists
import shutil

try:
    flask_secret_key = os.environ['FLASK_SECRET_KEY']
    print(f"flask_secret_key: {flask_secret_key}")
except:
    print("error")


camera_url = "http://192.168.2.32:8080"
storage_stub = "/ccapi/ver110/contents/sd/100CANON"
target_download_folder = "."
list_to_scan_webhook = "https://hook.integromat.com/w0svuv32ezecbsqvyp015x8rjisxx74u"
root_image_folder = "G:\Shared drives\PURPLEMANA_TEAMDRIVE_AP\images"
foldermill_qr = "G:\\Shared drives\\PURPLEMANA_TEAMDRIVE_AP\\foldermill\\qr_labels"

#lights
light1 = "192.168.2.183"
light2 = "192.168.2.224"
light3 = "192.168.2.205"
light4 = "192.168.2.56"
blacklight = "192.168.2.88"



def get_list_to_scan(list_to_scan_webhook):
    print(f"get_list_to_scan called")
    r = requests.get(list_to_scan_webhook)
    y = json.loads(r.content)
    print(y)

    list_builder = []

    for row in y:
        sku = row['sku']
        name = row['name']
        series = row['series']
        condition = row['condition']
        qr_label_url = row['qr_label_url']
        list_builder.append([sku, name, series, condition, qr_label_url])

    #return values(y)
    return list_builder

def get_all_files(camera_url, storage_stub):
    
    print (f"get_all_files called with camera_url: {camera_url}, storage_stub: {storage_stub}")
    r = requests.get(camera_url + storage_stub)
    y = json.loads(r.content)

    print(y)

    return y['path']


def delete_file(camera_url, path_to_file):
    x = requests.delete(camera_url + path_to_file)
    print(x.text)


def shutter_button(camera_url):
    shutter_url = "/ccapi/ver100/shooting/control/shutterbutton"
    payload = "{\"af\" : true}"
    #print(payload)
    x = requests.post(camera_url + shutter_url, data = payload)
    print (x)


def download_file(camera_url, path_to_download, output_file):
    print("download_file called")
    response = requests.get(camera_url + path_to_download, stream=False)

    with open(output_file, "wb") as handle:
        for data in tqdm(response.iter_content()):
            handle.write(data)


def download_and_erase_all_files(camera_url, path_to_download):
    print("download_and_erase_all_files called")
    all_files = get_all_files(camera_url, storage_stub)

    for file in all_files:
        print(f"deleting: {file}")

        filename = os.path.basename(file)
        print(f"filename: {filename}")

        print("downloading ..." + filename)
        download_file(camera_url, file, target_download_folder + "\\" + filename)
        print(f"done downloading {file}")

        print("deleting ..." + file)
        delete_file(camera_url,file)
        print('done')

        delete_file(camera_url,file)

    return True


def print_qr(folderpath):
    print(f"print_qr called with folderpath: {folderpath}")

    qrfile = "zz__" + selected_sku + "-label.jpg"
    qrpath = folderpath + "\\" + qrfile

    if exists(qrpath):
        #copy file to foldermill
        print(f"copying file to foldermill: {qrpath}")        
        print(f"foldermill: {foldermill_qr}")
        shutil.copy(folderpath + "\\" + qrfile, foldermill_qr)

    elif selected_qr_label_url:
        response = requests.get(selected_qr_label_url, stream=False)

        with open(folderpath + "\\" + qrfile, "wb") as handle:
            for data in tqdm(response.iter_content()):
                handle.write(data)
        
        print("now copy to foldermill")

    if exists(folderpath + "\\" + qrfile):
        image = Image.open(folderpath + "\\" + qrfile)
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window2["-QR-"].update(data=bio.getvalue())



def check_folder_for_images(folderpath):

    print("check_folder_for_images ..." + folderpath)

    front_file = "zz__raw-" + selected_sku + "-front.jpg"
    back_file = "zz__raw-" + selected_sku + "-back.jpg"
    qrfile = "zz__" + selected_sku + "-label.jpg"

    if exists(folderpath + "\\" + front_file):
        image = Image.open(folderpath + "\\" + front_file)
        image.thumbnail((600, 400))
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window2["-FRONT-"].update(data=bio.getvalue())


    if exists(folderpath + "\\" + back_file):
        image = Image.open(folderpath + "\\" + back_file)
        image.thumbnail((600, 400))
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window2["-BACK-"].update(data=bio.getvalue())

    if exists(folderpath + "\\" + qrfile):
        image = Image.open(folderpath + "\\" + qrfile)
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window2["-QR-"].update(data=bio.getvalue())




def take_photo(camera_url, sku, side):
    print(f"take_photo called with side: {side}")

    #check for folder
    if(os.path.isdir(root_image_folder + "\\" + sku)):
        print("folder exists")

    else:
        print("folder does not exist ... creating")
        os.mkdir(root_image_folder + "\\" + sku)

    #take photo
    shutter_button(camera_url)

    time.sleep(1.5)

    all_files = get_all_files(camera_url, storage_stub)

    for file in all_files:
        print(f"deleting: {file}")

        filename = os.path.basename(file)
        print(f"filename: {filename}")

        print("downloading ..." + filename)
        newfilename = "zz__raw-" + selected_sku + "-" + side + ".jpg"
        new_path_to_file = root_image_folder + "\\" + sku + "\\" + newfilename
        print(f"new_path_to_file: {new_path_to_file}")
        download_file(camera_url, file, new_path_to_file)

        print(f"done downloading {newfilename}")

        image = Image.open(new_path_to_file)
        image.thumbnail((800, 600))
        bio = io.BytesIO()
        image.save(bio, format="PNG")
        window2["-" + side.upper() + "-"].update(data=bio.getvalue())

        print("deleting ..." + file)
        delete_file(camera_url,file)
        print('done')

        delete_file(camera_url,file)


    return True


def toggle_light(light, delay):
    toggle_url = "http://" + light + "/cm?cmnd=Power%20TOGGLE"
    print (f"toggle_light called with light: {light}, delay: {delay}")
    r = requests.get(toggle_url)
    time.sleep(delay)
    r = requests.get(toggle_url)
    y = json.loads(r.content)

    print(y)

    return y

sg.theme('DarkAmber')   # Add a little color to your windows
# All the stuff inside your window. This is the PSG magic code compactor...


listvalues = get_list_to_scan(list_to_scan_webhook)
headings = ['sku', 'name', 'series', 'condition']

def make_win1():
    layout =    [
                [sg.Table(key="_itemstable_", values=listvalues, headings=headings, select_mode=sg.TABLE_SELECT_MODE_BROWSE, enable_events=True)],
                [sg.Button('Select')],
                [sg.Text('Folder'), sg.In(size=(25,1), enable_events=True ,key='-FOLDER-'), sg.FolderBrowse()],
                [sg.Button("Download and delete files")],
                ]
    return sg.Window('Purplemana: Image tools', layout, location=(1024,768), finalize=True)
def make_win2():
    layout = [[sg.Text('SKU: ' + selected_sku)],
              [sg.Image(key="-FRONT-"),sg.Image(key="-BACK-")],
              [sg.Image(key="-QR-")],
              [sg.Button("Take front photo"), sg.Button("Take back photo")],
              [sg.Button("Print QR Label"), sg.Button("Light1"), sg.Button("Light2"), sg.Button("Light3"), sg.Button("Light4"), sg.Button("Blacklight")],
              [sg.Button("Exit")]
              ]
    return sg.Window('Purplemana Image Tools: Item', layout, finalize=True)


#populate the list

window1, window2 = make_win1(), None        # start off with 1 window open


# Event Loop to process "events"
while True:             
    window, event, values = sg.read_all_windows()

    if event == '_itemstable_':
        row = listvalues[values['_itemstable_'][0]]
        selected_sku = row[0]
        selected_name = row[1]
        selected_series = row[2]
        selected_condition = row[3]
        selected_qr_label_url = row[4]
        print(f"selected sku: {row[0]}")

    if event == "Fire shutter":
        print ("Fire shutter button called")
        shutter_button(camera_url)

    if event == "Download and delete files":
        print ("Download and delete files button called")
        download_and_erase_all_files(camera_url, target_download_folder)

    if event == '-FOLDER-':
        load_folder = values['-FOLDER-']
        print(f"folder selected: {load_folder}")
        selected_sku = os.path.basename(load_folder)
        print(f"selected_sku: {selected_sku}")

        window2 = make_win2()
        check_folder_for_images(load_folder)

    if event == sg.WIN_CLOSED or event == 'Exit':
        window.close()
        if window == window2:       # if closing win 2, mark as closed
            window2 = None
        elif window == window1:     # if closing win 1, exit program
            break
    elif event == 'Select' and not window2:
        window2 = make_win2()
        check_folder_for_images(root_image_folder + "\\" + selected_sku)

    if event == "Take front photo":
        take_photo(camera_url, selected_sku, "front")

    elif event == "Take back photo":
        take_photo(camera_url, selected_sku, "back")

    elif event == "Print QR Label":
        print_qr(root_image_folder + "\\" + selected_sku)

    elif event == "Light1":
        toggle_light(light1, 3)

    elif event == "Light2":
        toggle_light(light2, 3)

    elif event == "Light3":
        toggle_light(light3, 3)

    elif event == "Light4":
        toggle_light(light4, 3)

    elif event == "Blacklight":
        toggle_light(blacklight, 3)


window.close()