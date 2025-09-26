import sys
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

# Import our existing core logic
sys.path.append(str(Path(__file__).parent.parent))
from ...core.processor import BatchRenameProcessor
from ...core.config import RenameConfig
class ProcessingThread(QThread):
    """Background thread for processing files to avoid GUI freezing."""
    
    finished = pyqtSignal(object)  # Emits RenameResult
    error = pyqtSignal(str)  # Emits error message
    
    def __init__(self, config: RenameConfig):
        super().__init__()
        self.config = config
    
    def run(self):
        """Execute the batch rename operation in background."""
        try:
            processor = BatchRenameProcessor()
            result = processor.process(self.config)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))