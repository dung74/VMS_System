#base_model.py
#base model inference for all AI models


class BaseModel(object):
    def __init__(self, model_name, confidence_threshold=0.5, model_path=None):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model_path = model_path


    
    def predict_frame(self, frame):
        """
        Predicts the frame using the model.
        This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this method.")
    