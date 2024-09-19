from pydicom.dataset import FileMetaDataset
from pynetdicom import AE, events, evt, debug_logger
from pynetdicom.sop_class import MRImageStorage
from queue import Queue

debug_logger()

class ModalityStoreSCP():
    def __init__(self) -> None:
        self.ae = AE(ae_title=b'STORESCP')
        self.scp = None
        self.queue = Queue()
        self._configure_ae()

    def _configure_ae(self) -> None:
        """Configure the Application Entity with the presentation context(s) which should be supported and start the SCP server.
        """
        handlers = [(evt.EVT_C_STORE, self.handle_store)]

        self.ae.add_supported_context(MRImageStorage)
        self.scp = self.ae.start_server(('127.0.0.1', 6667), block=False, evt_handlers=handlers)
        print("SCP Server started")

    def handle_store(self, event: events.Event) -> int:
        """Callable handler function used to handle a C-STORE event.

        Args:
            event (Event): Representation of a C-STORE event.

        Returns:
            int: Status Code
        """
        dataset = event.dataset
        dataset.file_meta = FileMetaDataset(event.file_meta)

        # TODO: Do something with the dataset. Think about how you can transfer the dataset from this place 

        # Add the received dataset to the queue for thread-safe and asynchronous processing.
        # This allows the dataset to be handled later while ensuring multiple datasets can be processed concurrently.
        self.queue.put(dataset)
        print(f"Dataset with SeriesInstanceUID {dataset.SeriesInstanceUID} received and added to the queue.")

        return 0x0000
