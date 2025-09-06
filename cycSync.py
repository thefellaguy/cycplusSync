import asyncio
import logging
from bleak import BleakScanner, BleakClient
import re

TARGET_NAME = "M1_74F7"
CHARACTERISTIC_UUID = "6e400004-b5a3-f393-e0a9-e50e24dcca9e"
CHARACTERISTIC_UUIDTX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
CHARACTERISTIC_UUIDRX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

VALUE_TO_WRITE = bytearray([0x05, 0x66, 0x69, 0x6c, 0x65, 0x6c, 0x69, 0x73, 0x74, 0x2e, 0x74, 0x78, 0x74, 0x57])
VALUE_TO_WRITE_DISKSPACE = bytearray([0x09, 0x00, 0x09])
VALUE_TO_WRITE_READ = bytearray([0xff, 0x00, 0xff])
VALUE_TO_WRITE_COPY = bytearray([0x43])
VALUE_TO_WRITE_COPYOK = bytearray([0x06])
VALUE_TO_WRITE_COPYOKOK = bytearray([0x15])
AWAIT_NEW_DATA = bytearray([0x41, 0x77, 0x61, 0x69, 0x74, 0x4E, 0x65, 0x77, 0x44, 0x61, 0x74, 0x61])

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BluetoothFileTransfer:
    def __init__(self):
        self.combine = False
        self.reply_ok = False
        self.data = bytearray()
        self.file_check = bytearray()
        self.trigger = False
        self.count = 0
        self.notification_data = bytearray()

    def reset_transfer_state(self):
        """Reset state variables before each file transfer"""
        self.combine = False
        self.reply_ok = False
        self.data = bytearray()
        self.file_check = bytearray()
        self.trigger = False
        self.count = 0
        self.notification_data = bytearray()

    def create_notification_handler(self):
        async def notification_handler(sender, data):
            logger.debug(f"Notification from {sender}: {data.hex()}")
            self.notification_data = data
            
            if CHARACTERISTIC_UUID in str(sender):
                if data == bytearray(b'\x04'):
                    return
                file_data = data[:-1]  # Remove the last byte
                if file_data == self.file_check:
                    logger.info(f"File request acknowledged: {file_data.hex()}")
                    self.reply_ok = True
                return
            
            if data == bytearray(b'\x04'):
                logger.info("End of data marker received")
                self.combine = False
                self.count = 6
                return
            
            if self.trigger:
                data = data[3:]
                self.trigger = False
            
            if self.combine:
                self.data.extend(data)
                self.count += 1
                logger.debug(f"Data chunk {self.count}: {len(data)} bytes")
        
        return notification_handler

    async def discover_device(self, target_name):
        logger.info("Scanning for Bluetooth devices...")
        devices = await BleakScanner.discover()
        for device in devices:
            logger.info(f"Found device: {device.name} - {device.address}")
            if device.name == target_name:
                logger.info(f"Found target device: {device.name} - {device.address}")
                return device
        logger.warning(f"Device with name {target_name} not found.")
        return None

    async def start_notify(self, client, uuid):
        try:
            await client.start_notify(uuid, self.create_notification_handler())
        except Exception as e:
            logger.error(f"Failed to start notifications: {e}")

    async def send_cmd(self, client, uuid, value, delay):
        try:
            await client.write_gatt_char(uuid, value, False)
        except Exception as e:
            logger.error(f"Failed to write value to characteristic: {e}")
        await asyncio.sleep(delay)

    async def wait_until_data(self, client, timeout_seconds=10):
        i = 0
        max_iterations = timeout_seconds * 100  # 0.01 second intervals
        
        while self.notification_data == AWAIT_NEW_DATA:
            await asyncio.sleep(0.01)
            i += 1
            if i >= max_iterations:
                logger.error(f"Timeout waiting for notification data after {timeout_seconds} seconds")
                return False
        
        logger.debug(f"Received data after {i * 0.01:.2f} seconds")
        return True

    async def request_read_file(self, client):
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUID, VALUE_TO_WRITE_READ, 0.01)
        success = await self.wait_until_data(client)
        if not success:
            logger.error("Failed to get read permission")
        return success

    async def copy_copyok(self, client):
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPY, 0.01)
        await self.wait_until_data(client)
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPYOK, 0.01)

    async def copy_copyok_combine(self, client):
        while self.count <= 5:
            await asyncio.sleep(0.01)
        self.count = 0
        self.data = self.data[:-2]
        self.trigger = True
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPYOK, 0.01)

    async def end_of_transfer(self, client):
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPYOKOK, 0.01)
        await self.wait_until_data(client)
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPYOK, 0.01)
        await self.wait_until_data(client)
        
    async def get_filelist(self, client):
        # Request Allow File Reads
        success = await self.request_read_file(client)
        if not success:
            logger.error("Failed to get read permission for file list")
            return
            
        # Request Read filelist.txt
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUID, VALUE_TO_WRITE, 0.01)
        await self.wait_until_data(client)
        await self.copy_copyok(client)
        self.combine = True
        self.trigger = True
        await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPY, 0.01)
        while self.combine:
            await self.copy_copyok_combine(client)
        await self.end_of_transfer(client)
        self.save_file_raw("output.txt", self.data)
    
    async def sync_fitfile(self, client, fit_file):
        self.reset_transfer_state()  # Reset state before each file transfer
        logger.info(f"Attempting to sync file: {fit_file}")
        
        # Create the bytearray to request the file
        byte_array = bytearray([0x05]) + bytearray(fit_file, 'utf-8') + bytearray([0x50])
        # Create bytearray to verify answer
        self.file_check = bytearray([0x06]) + bytearray(fit_file, 'utf-8')
        
        logger.info(f"Request bytes: {byte_array.hex()}")
        logger.info(f"Expected response: {self.file_check.hex()}")
        
        # Request Read Permission
        success = await self.request_read_file(client)
        if not success:
            logger.error(f"Failed to get read permission for {fit_file}")
            return False
            
        # Request the File
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUID, byte_array, 0.01)
        success = await self.wait_until_data(client)
        
        if not success:
            logger.error(f"No response received for file request: {fit_file}")
            return False
        
        logger.info(f"Received notification: {self.notification_data.hex()}")
        logger.info(f"Reply OK status: {self.reply_ok}")
        
        if self.reply_ok:
            logger.info(f"Starting file transfer for {fit_file}")
            self.combine = False
            await self.copy_copyok(client)
            self.data = bytearray()
            self.combine = True
            self.trigger = True
            await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPY, 0.01)
            
            # Monitor the transfer
            transfer_timeout = 0
            while self.combine:
                await self.copy_copyok_combine(client)
                transfer_timeout += 1
                if transfer_timeout > 1000:  # Prevent infinite loop
                    logger.error(f"Transfer timeout for {fit_file}")
                    break
                    
            await self.end_of_transfer(client)
            
            if len(self.data) > 0:
                self.save_file_raw(fit_file, self.data)
                logger.info(f"Successfully saved {fit_file} ({len(self.data)} bytes)")
                return True
            else:
                logger.warning(f"No data received for {fit_file}")
                return False
        else:
            logger.warning(f"File request for {fit_file} was not acknowledged properly")
            return False
            
    async def read_diskspace(self, client):
        pre = bytearray(b'\n')
        # Read Diskspace
        self.notification_data = AWAIT_NEW_DATA
        await self.send_cmd(client, CHARACTERISTIC_UUID, VALUE_TO_WRITE_DISKSPACE, 0.01)
        await self.wait_until_data(client)
        if self.notification_data[:1] == pre:
            data = self.notification_data[1:-1].decode('utf-8')  # Decode bytearray to string
            logger.info(f"Free Diskspace: {data}kb")
            
    async def run(self):
        device = await self.discover_device(TARGET_NAME)
        if not device:
            return
            
        async with BleakClient(device.address) as client:
            if client.is_connected:
                logger.info(f"Connected to {device.name}")
                await asyncio.sleep(5)
                
                # Start Notification Services
                await self.start_notify(client, CHARACTERISTIC_UUID)
                await self.start_notify(client, CHARACTERISTIC_UUIDTX)
                logger.info(f"Notifications started")
                
                await self.read_diskspace(client)
                await self.get_filelist(client)
                
                fit_files = self.extract_fit_filenames("output.txt")
                logger.info(f"Found {len(fit_files)} FIT files to transfer: {list(fit_files)}")
                
                successful_transfers = 0
                failed_transfers = 0
                
                for i, fit_file in enumerate(fit_files, 1):
                    logger.info(f"Transferring file {i}/{len(fit_files)}: {fit_file}")
                    try:
                        success = await self.sync_fitfile(client, fit_file)
                        if success:
                            successful_transfers += 1
                            logger.info(f"Successfully transferred {fit_file}")
                        else:
                            failed_transfers += 1
                            logger.error(f"Failed to transfer {fit_file}")
                    except Exception as e:
                        failed_transfers += 1
                        logger.error(f"Exception during transfer of {fit_file}: {e}")
                    
                    # Small delay between transfers
                    await asyncio.sleep(2)
                
                logger.info(f"Transfer summary: {successful_transfers} successful, {failed_transfers} failed")
                
                await client.stop_notify(CHARACTERISTIC_UUID)
                await client.stop_notify(CHARACTERISTIC_UUIDTX)
                logger.info("All transfers completed")
            else:
                logger.error(f"Failed to connect to {device.name}")

    def extract_fit_filenames(self, file_path):
        fit_files = set()
        pattern = re.compile(r'\d{14}\.fit')
        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    match = pattern.search(line)
                    if match:
                        fit_files.add(match.group(0))
        except Exception as e:
            logger.error(f"Failed to read/parse file: {e}")
        return fit_files

    def save_file_raw(self, name, data):
        # Remove trailing null bytes
        while data and data[-1] == 0x00:
            data = data[:-1]
        try:
            with open(name, "wb") as file:
                file.write(data)
            logger.info(f"Successfully wrote {len(data)} bytes to {name}")
        except Exception as e:
            logger.error(f"Failed to write data to {name}: {e}")

if __name__ == "__main__":
    # Enable debug logging for more detailed output
    # Uncomment the line below if you want more verbose logging
    # logging.getLogger().setLevel(logging.DEBUG)
    
    # You can specify a custom download directory here
    # transfer = BluetoothFileTransfer(download_directory="./my_fit_files")
    transfer = BluetoothFileTransfer()  # Uses default "./fit_files" directory
    asyncio.run(transfer.run())
