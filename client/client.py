#!/usr/bin/python3

import socket as sk
import os
import traceback

SERVER_HOST = "localhost"
SERVER_PORT = 10000
UPLOAD_CHUNK = 4096
FILES_PATH = "./files/"

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def wait():
    input("\nPremi [INVIO] per continuare: ")

def sendMessage(sock, message, encode=True):
    sock.sendto(message.encode() if encode else message, (SERVER_HOST, SERVER_PORT))
    
# Creiamo il socket UDP e lo associamo alla variabile sock
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)

try:
    downloading_file = False
    while True:
        cls()
        print("1. Elenco dei file")
        print("2. Upload di un file")
        print("3. Download di un file")
        print("4. Esci")
        option = int(input(" > Seleziona un'opzione: "))
        print()
        
        match option:
            case 1: # Elenco dei file
                sendMessage(sock, "list")
                data, server = sock.recvfrom(4096)
                data = data.decode()
                print("File disponibili: ")
                for file in data.split(":"):
                    print("- "+file)
            case 2: # Upload di un file
                filename = input("Inserisci il nome del file da caricare: ")
                if os.path.exists(FILES_PATH+filename):
                    sendMessage(sock, "put start "+filename)
                    file = open(FILES_PATH+filename, "rb")
                    while True:
                        part = file.read(UPLOAD_CHUNK)
                        if not part:
                            break
                        sendMessage(sock, part, False)
                    file.close()
                    sendMessage(sock, "put end")
                    print("Upload del file \""+filename+"\" completato")
                else:
                    print("Il file selezionato non esiste")
            case 3: # Download di un file
                filename = input("Inserisci il nome del file da scaricare: ")
                sendMessage(sock, "get "+filename)
                data, server = sock.recvfrom(4096)
                if data.decode() == "get start":
                    print("Inizio download del file "+filename)
                    downloading_file = open(FILES_PATH+filename, "wb")
                    while True:
                        data, address = sock.recvfrom(4096)
                        # data è binario, perciò il confronto viene fatto su b"get end"
                        if data == b"get end":
                            downloading_file.close()
                            downloading_file = False
                            print("Download del file completato")
                            break
                        else:
                            downloading_file.write(data)
                            # Invio un messaggio per informare il server che il client è pronto ad una prossima ricezione
                            sendMessage(sock, "get ok")
                else:
                    print("Impossibile scaricare il file: "+data.decode())
            case 4:
                print("Termine esecuzione del programma")
                break
        wait()
except Exception as ex:
    print("Si è verificato un problema\n\t(DETTAGLIO: "+("".join(traceback.TracebackException.from_exception(ex).format()))+")")
finally:
    sock.close()