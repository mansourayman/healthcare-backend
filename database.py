from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base;
url="mysql+mysqlconnector://root@127.0.0.1:3306/health_monitoring"
engine=create_engine(url,echo=True)
sessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False);
Base=declarative_base();