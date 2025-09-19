import asyncio
import logging
from bleak import BleakScanner, BleakClient
import re
import os

TARGET_NAME = "M1_74F7"
TARGET_MAC_ADDRESS = ""  # Optional: specify MAC address if device name discovery fails
# Example: TARGET_MAC_ADDRESS = "F7:74:13:47:EA:36"
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
    def __init__(self, download_directory="."):
        self.combine = False
        self.reply_ok = False
        self.data = bytearray()
        self.file_check = bytearray()
        self.trigger = False
        self.count = 0
        self.notification_data = bytearray()
        self.download_directory = download_directory

        # Create download directory if it doesn't exist (only if not current directory)
        if download_directory != "." and not os.path.exists(self.download_directory):
            os.makedirs(self.download_directory)
            logger.info(f"Created download directory: {self.download_directory}")

        logger.info(f"Using download directory: {os.path.abspath(self.download_directory)}")

    def file_exists_locally(self, filename):
        """Check if a file already exists in the download directory"""
        filepath = os.path.join(self.download_directory, filename)
        exists = os.path.exists(filepath)
        if exists:
            file_size = os.path.getsize(filepath)
            logger.info(f"File {filename} already exists locally at {filepath} ({file_size} bytes)")
        else:
            logger.info(f"File {filename} does not exist locally at {filepath}")
        return exists

    def filter_new_files(self, fit_files):
        """Filter out files that already exist locally"""
        logger.info(f"Checking download directory: {os.path.abspath(self.download_directory)}")
        logger.info(f"Directory exists: {os.path.exists(self.download_directory)}")

        if os.path.exists(self.download_directory):
            existing_files_in_dir = os.listdir(self.download_directory)
            logger.info(f"Files currently in download directory: {existing_files_in_dir}")

        new_files = []
        existing_files = []

        for fit_file in fit_files:
            if self.file_exists_locally(fit_file):
                existing_files.append(fit_file)
            else:
                new_files.append(fit_file)

        logger.info(f"Filter results: {len(existing_files)} existing files, {len(new_files)} new files to download")
        if existing_files:
            logger.info(f"Skipping existing files: {existing_files}")
        if new_files:
            logger.info(f"New files to download: {new_files}")

        return new_files

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

    async def discover_device(self, target_name, target_mac=None):
        """Discover device by name or MAC address"""
        if target_mac:
            logger.info(f"Attempting to connect directly to MAC address: {target_mac}")

            # Create a mock device object for direct MAC connection
            class MockDevice:
                def __init__(self, address):
                    self.address = address
                    self.name = f"Device_{address}"

            return MockDevice(target_mac)

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

            try:
                self.combine = False
                await self.copy_copyok(client)
                self.data = bytearray()
                self.combine = True
                self.trigger = True
                await self.send_cmd(client, CHARACTERISTIC_UUIDRX, VALUE_TO_WRITE_COPY, 0.01)

                # Monitor the transfer with timeout protection
                transfer_timeout = 0
                last_data_size = 0
                stall_count = 0

                while self.combine:
                    await self.copy_copyok_combine(client)
                    transfer_timeout += 1

                    # Check for transfer progress
                    if len(self.data) > last_data_size:
                        last_data_size = len(self.data)
                        stall_count = 0
                        logger.debug(f"Transfer progress: {len(self.data)} bytes")
                    else:
                        stall_count += 1

                    # Break on timeout or stall
                    if transfer_timeout > 2000:  # Increased timeout for larger files
                        logger.error(f"Transfer timeout for {fit_file} after {transfer_timeout} iterations")
                        break
                    elif stall_count > 100:  # No progress for too long
                        logger.error(f"Transfer stalled for {fit_file} - no progress for {stall_count} iterations")
                        break

                await self.end_of_transfer(client)

            except Exception as e:
                logger.error(f"Error during transfer: {e}")

            if len(self.data) > 0:
                filepath = os.path.join(self.download_directory, fit_file)
                self.save_file_raw(filepath, self.data)
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

    async def connect_with_retry(self, device, max_retries=3, timeout=30):
        """Connect to device with retry logic and custom timeout"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Connection attempt {attempt + 1}/{max_retries} to {device.name}")

                # Create client with custom timeout
                client = BleakClient(device.address, timeout=timeout)
                await client.connect()

                if client.is_connected:
                    logger.info(f"Successfully connected to {device.name} on attempt {attempt + 1}")
                    return client
                else:
                    logger.warning(f"Connection attempt {attempt + 1} failed - client not connected")

            except asyncio.TimeoutError:
                logger.warning(f"Connection attempt {attempt + 1} timed out after {timeout} seconds")
                if attempt < max_retries - 1:
                    retry_delay = 5 + (attempt * 2)  # Progressive delay: 5, 7, 9 seconds
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    await asyncio.sleep(retry_delay)

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed with error: {e}")
                if attempt < max_retries - 1:
                    retry_delay = 5 + (attempt * 2)
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    await asyncio.sleep(retry_delay)

        logger.error(f"Failed to connect to {device.name} after {max_retries} attempts")
        return None

    async def run(self):
        # Debug: Test the file checking logic
        logger.info(f"DEBUG: Testing file existence check...")
        logger.info(f"DEBUG: Download directory: {os.path.abspath(self.download_directory)}")
        logger.info(f"DEBUG: Directory exists: {os.path.exists(self.download_directory)}")

        if os.path.exists(self.download_directory):
            files_in_dir = os.listdir(self.download_directory)
            logger.info(f"DEBUG: Files in directory: {files_in_dir}")

        device = await self.discover_device(TARGET_NAME, TARGET_MAC_ADDRESS if TARGET_MAC_ADDRESS else None)
        if not device:
            if TARGET_MAC_ADDRESS:
                logger.error(f"Unable to create device object for MAC address: {TARGET_MAC_ADDRESS}")
            else:
                logger.error(
                    "Device discovery failed. Consider setting TARGET_MAC_ADDRESS if you know the device's MAC address.")
            return

        # Use retry logic for connection
        client = await self.connect_with_retry(device)
        if not client:
            logger.error("Unable to establish connection after multiple attempts")
            return

        try:
            logger.info(f"Connected to {device.name}")
            await asyncio.sleep(5)

            # Start Notification Services
            await self.start_notify(client, CHARACTERISTIC_UUID)
            await self.start_notify(client, CHARACTERISTIC_UUIDTX)
            logger.info(f"Notifications started")

            await self.read_diskspace(client)
            await self.get_filelist(client)

            fit_files = self.extract_fit_filenames("output.txt")
            logger.info(f"Found {len(fit_files)} total FIT files on device: {list(fit_files)}")

            # Filter out files that already exist locally
            new_files = self.filter_new_files(fit_files)

            if not new_files:
                logger.info("No new files to download - all files already exist locally!")
                return

            logger.info(f"Will download {len(new_files)} new files: {new_files}")

            successful_transfers = 0
            failed_transfers = 0

            for i, fit_file in enumerate(new_files, 1):
                logger.info(f"Transferring file {i}/{len(new_files)}: {fit_file}")
                try:
                    success = await self.sync_fitfile(client, fit_file)
                    if success:
                        successful_transfers += 1
                        logger.info(f"✓ Successfully transferred {fit_file}")
                    else:
                        failed_transfers += 1
                        logger.error(f"✗ Failed to transfer {fit_file}")
                except Exception as e:
                    failed_transfers += 1
                    logger.error(f"✗ Exception during transfer of {fit_file}: {e}")

                # Small delay between transfers
                if i < len(new_files):  # Don't wait after the last file
                    logger.info(f"Waiting 2 seconds before next transfer...")
                    await asyncio.sleep(2)

            logger.info(f"Transfer summary: {successful_transfers} successful, {failed_transfers} failed")
            logger.info("All transfers completed")

        except Exception as e:
            logger.error(f"Error during transfer session: {e}")
        finally:
            # Always clean up notifications and disconnect
            try:
                if client.is_connected:
                    await client.stop_notify(CHARACTERISTIC_UUID)
                    await client.stop_notify(CHARACTERISTIC_UUIDTX)
                    await client.disconnect()
                    logger.info("Disconnected from device")
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")

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

    # Default behavior: save files in the same directory as the script
    # To use a subdirectory instead, uncomment the line below:
    # transfer = BluetoothFileTransfer(download_directory="./fit_files")
    transfer = BluetoothFileTransfer()  # Uses current directory
    asyncio.run(transfer.run())
