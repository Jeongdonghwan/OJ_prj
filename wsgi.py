from app import create_app
from config import ProdConfig

app = create_app(ProdConfig)
