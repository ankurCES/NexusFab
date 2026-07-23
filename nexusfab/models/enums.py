import enum


class PlantCategory(str, enum.Enum):
    WATER = "water"
    CONFECTIONERY = "confectionery"
    DAIRY = "dairy"
    PET_FOOD = "pet_food"
    PREPARED_FOODS = "prepared_foods"


class LineStatus(str, enum.Enum):
    RUNNING = "running"
    DOWN = "down"
    CHANGEOVER = "changeover"
    CIP = "cip"
    IDLE = "idle"
    MAINTENANCE = "maintenance"


class EquipmentType(str, enum.Enum):
    FILLER = "filler"
    CAPPER = "capper"
    LABELER = "labeler"
    CONVEYOR = "conveyor"
    MIXER = "mixer"
    PACKAGING = "packaging"
    PASTEURIZER = "pasteurizer"
    HOMOGENIZER = "homogenizer"
    DRYER = "dryer"


class DowntimeType(str, enum.Enum):
    MECHANICAL = "mechanical"
    ELECTRICAL = "electrical"
    PROCESS = "process"
    CHANGEOVER = "changeover"
    CIP = "cip"
    PLANNED_MAINTENANCE = "planned_maintenance"
    OTHER = "other"


class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    CONDITION_BASED = "condition_based"


class ABCClass(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"


class Allergen(str, enum.Enum):
    GLUTEN = "GLUTEN"
    DAIRY = "DAIRY"
    NUTS = "NUTS"
    SOY = "SOY"
    EGGS = "EGGS"
    SESAME = "SESAME"


class CIPClass(str, enum.Enum):
    NONE = "none"
    RINSE = "rinse"
    STANDARD = "standard"
    ALLERGEN = "allergen"
    DEEP_CLEAN = "deep_clean"
