from qbittorrent import Client
import bencoding, hashlib
import time
import requests
import torf
import os

# https://stackoverflow.com/questions/46025771/python3-calculating-torrent-hash

def download_magnet(link, folder):
    m = torf.Magnet.from_string(link)

    qb = Client('http://127.0.0.1:8080/')
    qb.login('admin', '123')
    link_list = [link]
    qb.download_from_link(link_list, savepath=folder)
    while 1:
        info = qb.get_torrent(m.infohash)
        if info['pieces_have'] == info['pieces_num']:
            return True


# download("magnet:?xt=urn:btih:10261b7e9d6b94d921bf1457f3a1c9bc4289bab3&dn=The%20Majesty%20of%20Our%20Broken%20Past&tr=http%3a%2f%2ftracker.bundles.bittorrent.com%2fannounce&tr=udp%3a%2f%2ftracker.openbittorrent.com%3a80%2fannounce&tr=udp%3a%2f%2ftracker.publicbt.com%3a80%2fannounce&ws=http%3a%2f%2fs3.amazonaws.com%2fcontent-bundles%2fproduction-df0ec56d-0fbb-bc2c-11e7-354ff3af9c4e%2fdb0df6be8d92bab21fca6a6a2ff32ac1484ea0eac5e4cec060204d2774043e63%2foriginals%2f", os.getcwd() + "/downloads")

