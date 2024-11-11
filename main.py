import argparse
import logging
import os
import shutil
import filecmp
import time
import signal
import sys
import threading

NMAXROUND = 10

def compareDir(source, replica):
    detectedSource = set(os.listdir(source))
    detectedReplica = set(os.listdir(replica))


    while True:
        currentSource = set(os.listdir(source))
        currentReplica = set(os.listdir(replica))

        newSource = currentSource - detectedSource
        newReplica = currentReplica - detectedReplica

        for f in newSource:
            logging.info(f"New file {f} detected in source directory")
            print(f"New file {f} detected in source!")
            detectedSource.add(f)

        for f in newReplica:
            logging.info(f"New file {f} detected in replica directory")
            print(f"New file {f} detected in replica!")
            detectedReplica.add(f)

        removedSource = detectedSource - currentSource
        removedReplica = detectedReplica - currentReplica

        for f in removedSource:
            logging.info(f"File {f} removed from source directory")
            print(f"File {f} removed from source!")
            detectedSource.remove(f)

        for f in removedReplica:
            logging.info(f"File {f} removed from replica directory")
            print(f"File {f} removed from replica!")
            detectedReplica.remove(f)
        
        time.sleep(1)



def signal_handler(sig, frame):
    logging.info('Sync interrupted by user with Ctrl+C.')
    print('Sync stopped by user!')
    if not checkSync(args.source, args.replica):
        logging.warning('Process ended with unsyncronized directories!')
        print('WARNING: process was ended with unsyncronized directories.')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def argsInput():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("replica")
    parser.add_argument("period")
    parser.add_argument("log")
    return parser.parse_args()


def logSetup(logPath):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(logPath)]
    )


def checkSync(source, replica):
    sourceFiles = set(os.listdir(source))
    replicaFiles = set(os.listdir(replica))

    
    for f in sourceFiles:
        sourcePath = os.path.join(source, f)
        replicaPath = os.path.join(replica, f)

        if not os.path.exists(replicaPath) or not filecmp.cmp(sourcePath, replicaPath, shallow=False):
            return False

    
    for f in replicaFiles:
        replicaPath = os.path.join(replica, f)
        if f not in sourceFiles:
            return False

    return True


def sync(source, replica):

    if not os.path.exists(source):
        logging.error(f"Source directory {source} doesn't exist.")
        sys.exit(1)

    if not os.path.exists(replica):
        logging.error(f"Replica directory {replica} doesn't exist.")
        sys.exit(1)


    sourceFiles = set(os.listdir(source))
    replicaFiles = set(os.listdir(replica))

    for f in sourceFiles:
        sourcePath = os.path.join(source, f)
        replicaPath = os.path.join(replica, f)

        if not os.path.exists(replicaPath) or not filecmp.cmp(sourcePath, replicaPath, shallow=False):
            try:
                shutil.copy2(sourcePath, replicaPath)
                logging.info(f"File {f} copied to replica")
                print(f'File {f} copied!')
            except Exception as e:
                logging.error(f"Error copying file {f}: {e}")

    for f in replicaFiles:
        if f not in sourceFiles:
            replicaPath = os.path.join(replica, f)
            try:
                os.remove(replicaPath)
                logging.info(f"File {f} removed from replica")
                print(f'File {f} removed!')
            except Exception as e:
                logging.error(f"Error removing file {f}: {e}")


def maxRounds(round_count):
    if round_count >= NMAXROUND:
        logging.warning(f"Max rounds ({NMAXROUND}) hit. Ending process.")
        sys.exit(0)

if __name__ == "__main__":
    args = argsInput()

    logSetup(args.log)
    logging.info("Start of directories sync")
    print("Start of the sync process!")

    interval = int(args.period)

    comparison_thread = threading.Thread(target=compareDir, args=(args.source, args.replica))
    comparison_thread.daemon = True
    comparison_thread.start()

    roundCount = 0

    while True:
        maxRounds(roundCount)

        sync(args.source, args.replica)
        logging.info(f"Sync finished. Waiting {interval} seconds until next sync.")
        print(f'Sync process finished. Restarting after {interval} seconds!')
        time.sleep(interval)

        roundCount += 1
