#!/usr/bin/python3

import socket as sk
import os

SERVER_HOST = "localhost"
SERVER_PORT = 10000
UPLOAD_CHUNK = 4096
FILES_PATH = "./files/"

def cls(): # Svuota il terminale
    os.system("cls" if os.name == "nt" else "clear")

def wait(): # Attesa di un input dell'utente
    input("\n\x1b[36;40mPremi [INVIO] per continuare: \x1b[0m")

def sendMessage(sock, message, encode=True): # Invio di un messaggio al server
    sock.sendto(message.encode() if encode else message, (SERVER_HOST, SERVER_PORT))

def info(message): # Messaggio di informazione (azzurro)
    header()
    print("\x1b[30;46m "+message.upper()+" \x1b[0m\n")
    
def success(message): # Messaggio di successo (verde)
    print("\x1b[32;40m"+message+"\x1b[0m")

def error(message): # Messaggio di errore (rosso)
    print("\x1b[31;40m"+message+"\x1b[0m")

def header(): # Stampa dei dati di intestazione
    cls()
    print("\x1b[30;43m", end="")
    print("                                  ")
    print("   Cardone,   Marco, 0000975894   ")
    print("   Desiderio, Marco, 0000839614   ")
    print("                                  ")
    print("           CLOUD CLIENT           ")
    print("                                  ")
    print("\x1b[0m")

# Variabili di gestione:
# - sock per gestire la comunicazione UDP
# - upload_available per gestire la possibilità di caricare file sul server
# - downloading_file per mantenere il riferimento al file durante l'operazione di download
# - option per la gestione degli input dell'utente
sock = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
upload_available = True
downloading_file = False
option = ""

# Controllo dell'esistenza della cartella per il caricamento dei file
while upload_available and not os.path.isdir(FILES_PATH):
    if option.casefold() != "retry":
        header()
        error("ATTENZIONE: La cartella designata come sorgente per l'upload dei file non esiste")
        print("Il programma può crearla automaticamente ma se decidi di non farlo, la funzione di upload non sarà disponibile")
        option = str(input("\n\x1b[36;40m > Vuoi creare la cartella \""+FILES_PATH+"\"? [SI/NO]:\x1b[0m "))
    match option.casefold():
        case "si" | "retry":
            # Tentativo di creazione della cartella e termine del ciclo di richiesta
            try:
                os.mkdir(FILES_PATH)
                success("La cartella "+FILES_PATH+" è stata creata con successo")
                wait()
                break
            except Exception as ex:
                while True:
                    error("Si è verificato un problema durante la creazione della cartella "+FILES_PATH+"\n > "+str(ex))
                    option = str(input("\n\x1b[36;40m > Vuoi riprovare? [SI/NO]:\x1b[0m "))
                    if option.casefold() == "no":
                        upload_available = False
                        break
                    elif option.casefold() == "si":
                        option = "RETRY"
                        break
        case "no":
            # Disattivazione dell'opzione di upload
            upload_available = False
        case _:
            error("L'opzione selezionata non è valida")
            wait()
# Avviso all'utente
if not upload_available:
    error("\nIl programma verrà avviato comunque ma la funzionalità di upload non sarà disponibile")
    wait()

# Ciclo principale del programma
try:
    while True:
        header()
        print("1. Elenco dei file nel cloud")
        print("2. Upload di un file"+(" \x1b[0;31;40m[NON DISPONIBILE]\x1b[0m" if not upload_available else ""))
        print("3. Download di un file")
        print("0. Esci")
        # Input gestito come stringa per poter gestire gli errori evitando il try-catch sul tipo di eccezione ValueError
        option = input("\n\x1b[36;40m > Seleziona un'opzione:\x1b[0m ")
        
        # try-catch per gestire gli errori (es. Server non avviato)
        # Inserito qui per permettere all'utente di continuare ad eseguire operazioni
        try:
            match option:
                case "1":
                    info("Elenco dei file nel cloud")
                    sendMessage(sock, "list")
                    data, server = sock.recvfrom(4096)
                    data = data.decode()
                    success("File disponibili: ")
                    if len(data) == 0:
                        print(" > Nessun file caricato nel cloud")
                    else:
                        for file in data.split(":"):
                            print("- "+file)
                case "2":
                    info("Upload di un file")
                    if not upload_available:
                        error("L'operazione di upload non è disponibile")
                    else:
                        filename = input("\x1b[36;40m > Inserisci il nome del file da caricare:\x1b[0m ")
                        if os.path.exists(FILES_PATH+filename):
                            sendMessage(sock, "put start "+filename)
                            file = open(FILES_PATH+filename, "rb")
                            while True:
                                part = file.read(UPLOAD_CHUNK)
                                if not part:
                                    break
                                sendMessage(sock, part, False)
                                # Attendo che il server mi dica che è pronto al prossimo invio
                                sock.recvfrom(4096)
                            file.close()
                            sendMessage(sock, "put end")
                            success("Upload del file \""+filename+"\" completato")
                        else:
                            error("Il file selezionato non esiste")
                case "3":
                    info("Download di un file")
                    filename = input("\x1b[36;40m > Inserisci il nome del file da scaricare:\x1b[0m ")
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
                                success("Download del file completato")
                                break
                            else:
                                downloading_file.write(data)
                                # Invio un messaggio per informare il server che il client è pronto ad una prossima ricezione
                                sendMessage(sock, "get ok")
                    else:
                        error("Impossibile scaricare il file: "+data.decode())
                case "0":
                    success("\nTermine esecuzione del programma")
                    break
                case _:
                    error("\nL'opzione selezionata non è valida")    
        except Exception as ex:
            error("Si è verificato un problema\n > "+str(ex))
        wait()
except Exception as ex:
    error("Si è verificato un problema\n > "+str(ex))
finally:
    sock.close()