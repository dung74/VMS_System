
import os

class ModelFactory:
    

    MODEL_MAPPING = {
        'person_card': 'ai_models.person_card.PersonCardPredictor',
        'cell_phone': 'ai_models.cell_phone.CellPhonePredictor'
    }

    PARAMETER_MAPPING_DEFAULT = {
        'person_card': {
            'confidence_threshold': 0.5,
            'model_path': 'models/best(33).pt',
            'class_person': 2,
            'class_card': 3
        },
        'cell_phone': {
            'confidence_threshold': 0.5,
            'model_path': 'models/yolov8n.pt',
        }
    }



    @classmethod
    def _get_model_type(cls, model_type):
        if model_type in cls.MODEL_MAPPING:
            return cls.MODEL_MAPPING[model_type]
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
    
    @classmethod
    def _get_model_parameters(cls, model_type):
        if model_type in cls.PARAMETER_MAPPING_DEFAULT:
            return cls.PARAMETER_MAPPING_DEFAULT[model_type]
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
    @classmethod
    def create_model_instance(cls, model_type, parameters=None):
        model_class_path = cls._get_model_type(model_type)
        model_parameters = cls._get_model_parameters(model_type)
        model_path = model_parameters.get('model_path')

        if model_path and not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at path: {model_path}")
        
        # Dynamically import the model class
        module_path, class_name = model_class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        model_class = getattr(module, class_name)
        return model_class(**model_parameters)
        
