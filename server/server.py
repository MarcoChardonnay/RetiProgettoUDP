#!/usr/bin/python3

import socket as sk
from datetime import datetime
import os

SERVER_HOST = "localhost"
SERVER_PORT = 10000
UPLOAD_CHUNK = 4096
FILES_PATH = "./files/" # Cartella in cui si trovano i file in condivisione

def cls(): # Svuota il terminale
    os.system("cls" if os.name == "nt" else "clear")

def log(message, address=False): # Stampa di un messaggio formattato
    print("\x1b[0;36m["+datetime.now().strftime("%d/%m/%Y %H:%M:%S")+"]"+(" ["+address[0]+":"+str(address[1])+"]" if address else "")+"\x1b[0m "+message)

def sendMessage(sock, address, message, encode=True): # Invio di un messaggio ad un client
    try:
        sock.sendto(message.encode() if encode else message, address)
    except Exception:
        log("Client non raggiungibile", address)

# Variabili di gestione:
# - sock per gestire la comunicazione UDP
# - checks_success per la gestione degli errori pre-avvio
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
checks_success = True

# Intestazione
cls()
print("\x1b[30;43m", end="")
print("                                  ")
print("   Cardone,   Marco, 0000975894   ")
print("   Desiderio, Marco, 0000839614   ")
print("                                  ")
print("           CLOUD SERVER           ")
print("                                  ")
print("\x1b[0m")
log("Avvio del server in corso")

# Controllo dell'esistenza della cartella del sistema "cloud"
if not os.path.isdir(FILES_PATH):
    try:
        os.mkdir(FILES_PATH)
        log("Creata la cartella del cloud \""+FILES_PATH+"\"")
    except Exception as ex:
        log("Si è verificato un problema durante la creazione della cartella "+FILES_PATH+"\n > "+str(ex))
        checks_success = False

if checks_success:
    try:
        #associamo il socket alla porta e avviamo il server
        sock.bind((SERVER_HOST, SERVER_PORT))
        log("Server in ascolto su "+SERVER_HOST+":"+str(SERVER_PORT))

        uploading_file = {}
        # Ciclo che attenderà i messaggi in entrata dal client
        while True:
            # Comandi disponibili:
            # - list
            # - put start <filename>
                # - <file_part>
            # - put end
            # - get <filename>

            data, address = sock.recvfrom(4096)

            if address[1] in uploading_file:
                # data è binario, perciò il confronto viene fatto su b"put end"
                if data == b"put end":
                    uploading_file[address[1]].close()
                    del uploading_file[address[1]]
                    log("Upload del file completato", address)
                else:
                    uploading_file[address[1]].write(data)
                    # Invio un messaggio per informare il client che il server è pronto ad una prossima ricezione
                    sendMessage(sock, address, "put ok")
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
                            uploading_file[address[1]] = open(FILES_PATH+filename, "wb")
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
        log("Si è verificato un problema\n > \x1b[31m"+str(ex)+"\x1b[0m")
    finally:
        sock.close()