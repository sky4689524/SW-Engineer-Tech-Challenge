import asyncio
import time
from pydicom import Dataset
from scp import ModalityStoreSCP
import aiohttp


class SeriesCollector:
    """A Series Collector is used to build up a list of instances (a DICOM series) as they are received by the modality.
    It stores the (during collection incomplete) series, the Series (Instance) UID, the time the series was last updated
    with a new instance and the information whether the dispatch of the series was started.
    """

    def __init__(self, first_dataset: Dataset) -> None:
        """Initialization of the Series Collector with the first dataset (instance).

        Args:
            first_dataset (Dataset): The first dataset or the regarding series received from the modality.
        """
        self.series_instance_uid = first_dataset.SeriesInstanceUID
        self.series: list[Dataset] = [first_dataset]
        self.last_update_time = time.time()
        self.dispatch_started = False

    def add_instance(self, dataset: Dataset) -> bool:
        """Add an dataset to the series collected by this Series Collector if it has the correct Series UID.

        Args:
            dataset (Dataset): The dataset to add.

        Returns:
            bool: `True`, if the Series UID of the dataset to add matched and the dataset was therefore added, `False` otherwise.
        """
        if self.series_instance_uid == dataset.SeriesInstanceUID:
            self.series.append(dataset)
            self.last_update_time = time.time()
            return True

        return False


class SeriesDispatcher:
    """This code provides a template for receiving data from a modality using DICOM.
    Be sure to understand how it works, then try to collect incoming series (hint: there is no attribute indicating how
    many instances are in a series, so you have to wait for some time to find out if a new instance is transmitted).
    For simplyfication, you can assume that only one series is transmitted at a time.
    You can use the given template, but you don't have to!
    """

    def __init__(self) -> None:
        """Initialize the Series Dispatcher.
        """

        self.loop: asyncio.AbstractEventLoop
        self.modality_scp = ModalityStoreSCP()
        # Dictionary to track series collectors by their SeriesInstanceUID to handle multiple series
        self.series_collectors = {}

    async def main(self) -> None:
        """An infinitely running method used as hook for the asyncio event loop.
        Keeps the event loop alive whether or not datasets are received from the modality and prints a message
        regulary when no datasets are received.
        """
        while True:
            # TODO: Regulary check if new datasets are received and act if they are.
            # Information about Python asyncio: https://docs.python.org/3/library/asyncio.html
            # When datasets are received you should collect and process them
            # (e.g. using `asyncio.create_task(self.run_series_collector()`)

            # Check if there are new datasets
            if not self.modality_scp.queue.empty():
                dataset = self.modality_scp.queue.get()
                await self.run_series_collectors(dataset)
            else:
                print("Waiting for Modality")

            # Periodically check for dispatching the series
            await self.dispatch_series_collector()

            await asyncio.sleep(0.2)

    async def run_series_collectors(self, dataset) -> None:
        """Processes the incoming DICOM dataset and adds it to the corresponding series.

        Args:
            dataset (Dataset): The incoming DICOM dataset.
        """
        # TODO: Get the data from the SCP and start dispatching
        series_uid = dataset.SeriesInstanceUID

        # Check if we already have a SeriesCollector for this series UID
        if series_uid not in self.series_collectors:
            # Create a new SeriesCollector if it doesn't exist or if it's a new series
            print(
                f"New series started instance {dataset.SOPInstanceUID}: {series_uid}")
            self.series_collectors[series_uid] = SeriesCollector(dataset)
        else:
            # Add the dataset to the existing collector
            added = self.series_collectors[series_uid].add_instance(dataset)
            if added:
                print(
                    f"Added instance {dataset.SOPInstanceUID} to series: {series_uid}")
            else:
                print(
                    f"Series UID mismatch for dataset, discarding dataset: {series_uid}")

    async def dispatch_series_collector(self) -> None:
        """Tries to dispatch a Series Collector, i.e. to finish it's dataset collection and scheduling of further
        methods to extract the desired information.
        """
        # Check if the series collector hasn't had an update for a long enough timespan and send the series to the
        # server if it is complete
        # NOTE: This is the last given function, you should create more for extracting the information and
        # sending the data to the server

        maximum_wait_time = 1
        current_time = time.time()
        series_to_dispatch = []

        # Iterate over all series collectors to check which series are ready for dispatch
        for series_uid, collector in list(self.series_collectors.items()):
            time_since_last_update = current_time - collector.last_update_time
            if time_since_last_update > maximum_wait_time and not collector.dispatch_started:
                # Mark the dispatch as started to avoid duplicate processing
                collector.dispatch_started = True
                print(f"Dispatching series: {collector.series_instance_uid}")
                series_to_dispatch.append(series_uid)

        # Dispatch all series that are ready for dispatch and remove them from the collector
        for series_uid in series_to_dispatch:
            await self.extract_and_send_series_info(self.series_collectors[series_uid])
            del self.series_collectors[series_uid]

    async def extract_and_send_series_info(self, collector: SeriesCollector) -> None:
        """Extracts the series metadata and sends it to the server.

        Args:
            collector (SeriesCollector): The SeriesCollector object containing the series' DICOM datasets.
        """

        # Extract metadata from the first dataset
        first_dataset = collector.series[0]
        patient_id = str(first_dataset.PatientID)
        patient_name = str(first_dataset.PatientName)
        study_instance_uid = str(first_dataset.StudyInstanceUID)
        series_instance_uid = str(collector.series_instance_uid)
        num_instances = len(collector.series)

        # Prepare the data to send to the server
        data = {
            'PatientID': patient_id,
            'PatientName': patient_name,
            'StudyInstanceUID': study_instance_uid,
            'SeriesInstanceUID': series_instance_uid,
            'InstanceInSeries': num_instances
        }

        # Send data to the server to store them into database
        await self.send_data_to_server(data)

    async def send_data_to_server(self, data: dict) -> None:
        """Sends the extracted series metadata to the server for storage.

        Args:
            data (dict): The series metadata to send.
        """
        url = 'http://localhost:8000/series'  # server URL

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                if response.status == 200:
                    # Parse the JSON response from the server
                    response_data = await response.json()
                    print(
                        f"Successfully sent data to the server: {response.status}")
                    print(f"Server message: {response_data.get('message')}")
                else:
                    print(
                        f"Failed to send data to the server: {response.status}")
                    print(f"Response text: {await response.text()}")


if __name__ == "__main__":
    """Create a Series Dispatcher object and run it's infinite `main()` method in a event loop.
    """
    engine = SeriesDispatcher()
    engine.loop = asyncio.get_event_loop()
    engine.loop.run_until_complete(engine.main())
