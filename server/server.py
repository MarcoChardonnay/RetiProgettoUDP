#!/usr/bin/python3

import socket as sk
from datetime import datetime
import os
import traceback

SERVER_HOST = "localhost"
SERVER_PORT = 10000
UPLOAD_CHUNK = 4096
FILES_PATH = "./files/" # Cartella in cui si trovano i file in condivisione

def log(message, address=False):
    #print("["+datetime.now().strftime("%m/%d/%Y %H:%M:%S")+"] "+("["+address[0]+":"+str(address[1])+"] " if address else "")+message)
    print("\033[95m["+datetime.now().strftime("%m/%d/%Y %H:%M:%S")+"] "+("\033[93m["+address[0]+":"+str(address[1])+"] " if address else "")+"\033[96m\033[1m"+message+"\x1b[0m")

def sendMessage(sock, address, message, encode=True):
    sock.sendto(message.encode() if encode else message, address)

# Creiamo il socket UDP e lo associamo alla variabile sock
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

log("Avvio del server in corso")
try:
    #associamo il socket alla porta e avviamo il server
    sock.bind((SERVER_HOST, SERVER_PORT))
    log("Server in ascolto su "+SERVER_HOST+":"+str(SERVER_PORT))

    uploading_file = False
    # Ciclo che attenderà i messaggi in entrata dal client
    while True:
        # Comandi disponibili:
        # - list
        # - put start <filename>
            # - <file_part>
        # - put end
        # - get <filename>

        data, address = sock.recvfrom(4096)

        if uploading_file:
            # data è binario, perciò il confronto viene fatto su b"put end"
            if data == b"put end":
                uploading_file.close()
                uploading_file = False
                log("Upload del file completato", address)
            else:
                uploading_file.write(data)
        else:
            data = data.decode().split(" ")
            match data[0]:
                case "list":
                    log("Richiesta la lista dei file", address)
                    files = []
                    for entry in os.scandir(FILES_PATH):
                        if entry.is_file(): # Solo se è un file
                            files.append(entry.name)
                    # Usiamo i due punti per separare perché non sono un carattere ammissibile nei nomi dei file
                    sock.sendto(":".join(files).encode(), address)
                case "put":
                    if data[1] == "start":
                        # Uniamo in filename tutti i pezzi di data dal secondo in poi
                        filename = " ".join(data[2:])
                        log("Inizio upload del file \""+filename+"\"", address)
                        uploading_file = open(FILES_PATH+filename, "wb")
                case "get":
                    filename = " ".join(data[1:])
                    log("Richiesto download del file \""+filename+"\"", address)
                    if os.path.exists(FILES_PATH+filename):
                        sendMessage(sock, address, "get start")
                        file = open(FILES_PATH+filename, "rb")
                        while True:
                            # Leggo il file chunk per chunk (4096 bytes alla volta) e li spedisco
                            part = file.read(UPLOAD_CHUNK)
                            if not part:
                                break
                            sendMessage(sock, address, part, False)
                            # Attendo che il client mi dica che è pronto al prossimo invio
                            sock.recvfrom(4096)
                        file.close()
                        sendMessage(sock, address, "get end")
                        log("Download del file \""+filename+"\" completato", address)
                    else:
                        log("Il file selezionato non esiste", address)
                        sendMessage(sock, address, "Il file \""+filename+"\" non esiste")
except Exception as ex:
    log("Si è verificato un problema\n\t(DETTAGLIO: "+("".join(traceback.TracebackException.from_exception(ex).format()))+")")
finally:
    sock.close()