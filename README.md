# cycplusSync
Pulls fit files ogg your cycplus M1 bicycle computer


This is largely based off of Kaiserdragon2 CycSync android app ( https://github.com/Kaiserdragon2/CycSync), only re-purposed to download the FIT files directly to your computer. From here you can do what you wish with them, includding upload them to strava. I personally view them locally with Fit File Viewer: https://github.com/Nick2bad4u/FitFileViewer


Usage: ust run the pythin file. If it doesn;t fibd your bike computer you might have to find the name of it and change like 6. Id you don't have a cycplus M1, you'll definitely have to change line 6. This is bluetooth LE, file transfers are not very fast. 

output:
```
python cycsync2.py 
2025-09-06 01:19:43,404 - INFO - Scanning for Bluetooth devices...
2025-09-06 01:19:48,432 - INFO - Found device: None - 3B:92:5B:B5:D8:1F
2025-09-06 01:19:48,433 - INFO - Found device: None - 54:D9:45:2F:D1:88
2025-09-06 01:19:48,433 - INFO - Found device: OKIN-084374 - FF:E6:AB:19:C6:B4
2025-09-06 01:19:48,433 - INFO - Found device: M1_74F7 - F7:74:13:47:EA:36
2025-09-06 01:19:48,433 - INFO - Found target device: M1_74F7 - F7:74:13:47:EA:36
2025-09-06 01:19:52,449 - INFO - Connected to M1_74F7
2025-09-06 01:19:58,636 - INFO - Notifications started
2025-09-06 01:19:59,156 - INFO - Free Diskspace: 15164/16384kb
2025-09-06 01:20:01,937 - INFO - End of data marker received
2025-09-06 01:20:02,950 - INFO - End of data marker received
2025-09-06 01:20:03,464 - INFO - Successfully wrote 160 bytes to output.txt
2025-09-06 01:20:03,465 - INFO - Found 6 FIT files to transfer: ['20250903184128.fit', '20250823061940.fit', '20250823082404.fit', '20250902062606.fit', '20250905164207.fit', '20250826085008.fit']
2025-09-06 01:20:03,465 - INFO - Transferring file 1/6: 20250903184128.fit
2025-09-06 01:20:03,465 - INFO - Attempting to sync file: 20250903184128.fit
2025-09-06 01:20:03,465 - INFO - Request bytes: 0532303235303930333138343132382e66697450
2025-09-06 01:20:03,465 - INFO - Expected response: 0632303235303930333138343132382e666974
2025-09-06 01:20:04,474 - INFO - File request acknowledged: 0632303235303930333138343132382e666974
2025-09-06 01:20:04,476 - INFO - Received notification: 0632303235303930333138343132382e6669745a
2025-09-06 01:20:04,476 - INFO - Reply OK status: True
2025-09-06 01:20:04,476 - INFO - Starting file transfer for 20250903184128.fit
2025-09-06 01:21:49,770 - INFO - End of data marker received
2025-09-06 01:21:50,277 - INFO - End of data marker received
2025-09-06 01:21:50,794 - INFO - Successfully wrote 114843 bytes to 20250903184128.fit
2025-09-06 01:21:50,794 - INFO - Successfully saved 20250903184128.fit (115710 bytes)
2025-09-06 01:21:50,794 - INFO - Successfully transferred 20250903184128.fit
2025-09-06 01:21:52,796 - INFO - Transferring file 2/6: 20250823061940.fit
2025-09-06 01:21:52,797 - INFO - Attempting to sync file: 20250823061940.fit
2025-09-06 01:21:52,797 - INFO - Request bytes: 0532303235303832333036313934302e66697450
2025-09-06 01:21:52,797 - INFO - Expected response: 0632303235303832333036313934302e666974
2025-09-06 01:21:53,831 - INFO - File request acknowledged: 0632303235303832333036313934302e666974
2025-09-06 01:21:53,832 - INFO - Received notification: 0632303235303832333036313934302e66697455
2025-09-06 01:21:53,832 - INFO - Reply OK status: True
2025-09-06 01:21:53,832 - INFO - Starting file transfer for 20250823061940.fit
2025-09-06 01:21:57,891 - INFO - End of data marker received
2025-09-06 01:21:58,399 - INFO - End of data marker received
2025-09-06 01:21:58,907 - INFO - Successfully wrote 2409 bytes to 20250823061940.fit
2025-09-06 01:21:58,907 - INFO - Successfully saved 20250823061940.fit (3070 bytes)
2025-09-06 01:21:58,907 - INFO - Successfully transferred 20250823061940.fit
2025-09-06 01:22:00,908 - INFO - Transferring file 3/6: 20250823082404.fit
2025-09-06 01:22:00,909 - INFO - Attempting to sync file: 20250823082404.fit
2025-09-06 01:22:00,909 - INFO - Request bytes: 0532303235303832333038323430342e66697450
2025-09-06 01:22:00,909 - INFO - Expected response: 0632303235303832333038323430342e666974
2025-09-06 01:22:01,698 - INFO - File request acknowledged: 0632303235303832333038323430342e666974
2025-09-06 01:22:01,703 - INFO - Received notification: 0632303235303832333038323430342e66697455
2025-09-06 01:22:01,703 - INFO - Reply OK status: True
2025-09-06 01:22:01,704 - INFO - Starting file transfer for 20250823082404.fit
2025-09-06 01:24:12,633 - INFO - End of data marker received
2025-09-06 01:24:13,141 - INFO - End of data marker received
2025-09-06 01:24:13,660 - INFO - Successfully wrote 137733 bytes to 20250823082404.fit
2025-09-06 01:24:13,660 - INFO - Successfully saved 20250823082404.fit (138238 bytes)
2025-09-06 01:24:13,660 - INFO - Successfully transferred 20250823082404.fit
2025-09-06 01:24:15,662 - INFO - Transferring file 4/6: 20250902062606.fit
2025-09-06 01:24:15,662 - INFO - Attempting to sync file: 20250902062606.fit
2025-09-06 01:24:15,662 - INFO - Request bytes: 0532303235303930323036323630362e66697450
2025-09-06 01:24:15,662 - INFO - Expected response: 0632303235303930323036323630362e666974
2025-09-06 01:24:16,439 - INFO - File request acknowledged: 0632303235303930323036323630362e666974
2025-09-06 01:24:16,441 - INFO - Received notification: 0632303235303930323036323630362e66697459
2025-09-06 01:24:16,441 - INFO - Reply OK status: True
2025-09-06 01:24:16,441 - INFO - Starting file transfer for 20250902062606.fit
2025-09-06 01:27:16,350 - INFO - End of data marker received
2025-09-06 01:27:16,857 - INFO - End of data marker received
2025-09-06 01:27:17,374 - INFO - Successfully wrote 191431 bytes to 20250902062606.fit
2025-09-06 01:27:17,374 - INFO - Successfully saved 20250902062606.fit (191486 bytes)
2025-09-06 01:27:17,374 - INFO - Successfully transferred 20250902062606.fit
2025-09-06 01:27:19,376 - INFO - Transferring file 5/6: 20250905164207.fit
2025-09-06 01:27:19,377 - INFO - Attempting to sync file: 20250905164207.fit
2025-09-06 01:27:19,377 - INFO - Request bytes: 0532303235303930353136343230372e66697450
2025-09-06 01:27:19,377 - INFO - Expected response: 0632303235303930353136343230372e666974
2025-09-06 01:27:20,157 - INFO - File request acknowledged: 0632303235303930353136343230372e666974
2025-09-06 01:27:20,163 - INFO - Received notification: 0632303235303930353136343230372e6669745c
2025-09-06 01:27:20,163 - INFO - Reply OK status: True
2025-09-06 01:27:20,163 - INFO - Starting file transfer for 20250905164207.fit
```
